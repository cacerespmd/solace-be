
from io import BytesIO
from urllib.parse import urljoin, urlparse
import ipaddress
import re
import socket


import chromadb
import httpx
from openai import OpenAI
from pypdf import PdfReader

from app.core.config import settings


MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARACTERS = 200_000
MAX_REDIRECTS = 5

# Restrict downloads to supported, trusted document hosts.
# Add your own trusted storage domain here when needed.
TRUSTED_DOCUMENT_HOSTS = {
    "docs.google.com",
    "drive.google.com",
    "doc-0c-0k-docstext.googleusercontent.com",
}

TRUSTED_DOCUMENT_HOST_SUFFIXES = (
    ".googleusercontent.com",
)


def get_collection():
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR
    )

    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    

def get_store_policy_collection():
    """
    Separate ChromaDB collection for store policies
    and FAQs, using the existing persistent database.
    """
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR
    )

    return client.get_or_create_collection(
        name="solace_store_policies",
        metadata={"hnsw:space": "cosine"},
    )



def is_trusted_document_host(hostname):
    hostname = hostname.lower().rstrip(".")

    if hostname in TRUSTED_DOCUMENT_HOSTS:
        return True

    return any(
        hostname.endswith(suffix)
        for suffix in TRUSTED_DOCUMENT_HOST_SUFFIXES
    )


def validate_document_url(url):
    parsed = urlparse(url)

    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Document URL must use HTTPS")

    if parsed.username or parsed.password:
        raise ValueError(
            "Document URLs cannot contain credentials"
        )

    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid document URL port")

    if port not in (None, 443):
        raise ValueError(
            "Only HTTPS port 443 is allowed"
        )

    hostname = parsed.hostname.lower().rstrip(".")

    if not is_trusted_document_host(hostname):
        raise ValueError(
            "Document host is not on the trusted host list"
        )

    try:
        addresses = socket.getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        raise ValueError(
            "Unable to resolve document host"
        )

    if not addresses:
        raise ValueError(
            "Document host has no resolved addresses"
        )

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError(
                "Document host must resolve to a public IP"
            )


def normalize_document_url(url):
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError(
            "Only HTTPS document URLs are supported"
        )

    if parsed.hostname != "docs.google.com":
        return url

    match = re.fullmatch(
        r"/document/d/([A-Za-z0-9_-]+)(?:/.*)?",
        parsed.path,
    )

    if not match:
        raise ValueError(
            "Invalid Google Docs document URL"
        )

    document_id = match.group(1)

    return (
        "https://docs.google.com/document/d/"
        "{}".format(document_id)
        + "/export?format=pdf"
    )


def download_document(url):
    current_url = url

    # Redirects are handled manually so each destination
    # can be checked before the next request.
    with httpx.Client(
        follow_redirects=False,
        timeout=30.0,
        trust_env=False,
    ) as client:

        for _ in range(MAX_REDIRECTS + 1):
            validate_document_url(current_url)

            with client.stream(
                "GET",
                current_url,
            ) as response:

                if response.status_code in (
                    301,
                    302,
                    303,
                    307,
                    308,
                ):
                    location = response.headers.get(
                        "location"
                    )

                    if not location:
                        raise ValueError(
                            "Document redirect has no destination"
                        )

                    current_url = urljoin(
                        current_url,
                        location,
                    )

                    continue

                response.raise_for_status()

                content = bytearray()

                for chunk in response.iter_bytes():
                    content.extend(chunk)

                    if len(content) > MAX_DOCUMENT_BYTES:
                        raise ValueError(
                            "Document exceeds the 10 MB limit"
                        )

                return bytes(content)

    raise ValueError(
        "Too many document redirects"
    )


def extract_document_text(content, url):
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Google Docs export URLs don't end in .pdf.
    is_google_docs_export = (
        parsed.hostname == "docs.google.com"
        and "/export" in path
        and "format=pdf" in parsed.query.lower()
    )

    is_pdf = (
        path.endswith(".pdf")
        or is_google_docs_export
        or content.startswith(b"%PDF-")
    )

    if is_pdf:
        try:
            reader = PdfReader(
                BytesIO(content)
            )

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except Exception as exc:
            raise ValueError(
                "Unable to read PDF document: {}".format(
                    str(exc)
                )
            )

    elif path.endswith(".txt"):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(
                "TXT document must use UTF-8 encoding"
            )

    else:
        raise ValueError(
            "Only PDF, TXT, and Google Docs documents "
            "are supported"
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "No readable text found in document"
        )

    if len(text) > MAX_TEXT_CHARACTERS:
        raise ValueError(
            "Extracted text exceeds the allowed limit"
        )

    return text


def split_text(
    text,
    chunk_size=1000,
    overlap=150,
):
    if chunk_size <= overlap:
        raise ValueError(
            "Chunk size must exceed overlap"
        )

    chunks = []
    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def ingest_product_document(document, product):
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not configured"
        )

    # Convert Google Docs links into PDF export URLs.
    download_url = normalize_document_url(
        document.document_url
    )

    # Download the document, following validated redirects.
    content = download_document(
        download_url
    )

    # Extract text from PDF, TXT, or Google Docs export.
    text = extract_document_text(
        content,
        download_url,
    )

    # Split the document into searchable chunks.
    chunks = split_text(text)

    if not chunks:
        raise ValueError(
            "No searchable content found"
        )

    # Generate embeddings.
    openai_client = OpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    embedding_response = (
        openai_client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=chunks,
        )
    )

    embeddings = [
        item.embedding
        for item in embedding_response.data
    ]

    # Connect to ChromaDB.
    collection = get_collection()

    # Remove old chunks before re-indexing.
    collection.delete(
        where={
            "document_id": document.id
        }
    )

    # Generate unique chunk IDs.
    ids = [
        "document_{}_chunk_{}".format(
            document.id,
            index,
        )
        for index in range(len(chunks))
    ]

    # Attach product information to each chunk.
    metadatas = [
        {
            "document_id": document.id,
            "product_id": product.id,
            "product_name": product.name,
            "product_description": (
                product.description or ""
            ),
            "document_title": document.title,
            "source_url": document.document_url,
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    # Store searchable chunks and embeddings.
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {
        "document_id": document.id,
        "product_id": product.id,
        "chunks_created": len(chunks),
        "status": "indexed",
    }
