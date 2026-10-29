from unittest.mock import Mock

import chromadb
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api import product_documents as api
from app.database import Base
from app.models import Product, ProductDocument
from app.schemas.product_document import ProductDocumentCreate, ProductDocumentUpdate


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Product(id=1, name="Test webcam", sku="TEST", price=10))
        session.commit()
        yield session
    engine.dispose()


def payload():
    return ProductDocumentCreate(
        title="Warranty", document_url="https://docs.google.com/document/d/test/edit",
    )


def test_add_indexes_only_submitted_link(db, monkeypatch):
    ingest = Mock()
    monkeypatch.setattr(api, "ingest_product_document", ingest)
    result = api.create_product_document(1, payload(), db, None)
    ingest.assert_called_once_with(result, db.get(Product, 1))
    assert result.id is not None
    assert db.get(ProductDocument, result.id) is result


@pytest.mark.parametrize("error, status", [(ValueError("Unreadable document"), 422),
                                         (RuntimeError("Index unavailable"), 503)])
def test_failed_ingestion_does_not_save_document(db, monkeypatch, error, status):
    monkeypatch.setattr(api, "ingest_product_document", Mock(side_effect=error))
    with pytest.raises(HTTPException) as caught:
        api.create_product_document(1, payload(), db, None)
    assert caught.value.status_code == status
    assert db.scalars(select(ProductDocument)).all() == []


def test_replacing_link_reindexes_document(db, monkeypatch):
    ingest = Mock()
    monkeypatch.setattr(api, "ingest_product_document", ingest)
    document = api.create_product_document(1, payload(), db, None)
    ingest.reset_mock()
    api.update_product_document(1, document.id, ProductDocumentUpdate(
        document_url="https://docs.google.com/document/d/replacement/edit",
    ), db, None)
    ingest.assert_called_once_with(document, db.get(Product, 1))
    assert "replacement" in document.document_url


def test_failed_update_preserves_saved_link(db, monkeypatch):
    monkeypatch.setattr(api, "ingest_product_document", Mock())
    document = api.create_product_document(1, payload(), db, None)
    original_url = document.document_url
    monkeypatch.setattr(api, "ingest_product_document", Mock(side_effect=ValueError("Bad link")))
    with pytest.raises(HTTPException):
        api.update_product_document(1, document.id, ProductDocumentUpdate(
            document_url="https://docs.google.com/document/d/replacement/edit",
        ), db, None)
    assert document.document_url == original_url


def test_delete_removes_only_target_document_chunks(db, monkeypatch, tmp_path):
    monkeypatch.setattr(api, "ingest_product_document", Mock())
    document = api.create_product_document(1, payload(), db, None)
    other = api.create_product_document(1, payload(), db, None)
    document_id = document.id
    collection = chromadb.PersistentClient(path=str(tmp_path)).create_collection("delete_test")
    collection.add(
        ids=["target_0", "target_1", "other_0"],
        embeddings=[[1.0, 0.0]] * 3,
        documents=["Warranty", "Exclusions", "Other document"],
        metadatas=[{"document_id": document_id}, {"document_id": document_id},
                   {"document_id": other.id}],
    )
    monkeypatch.setattr(api, "get_collection", lambda: collection)
    api.delete_product_document(1, document_id, db, None)
    assert db.get(ProductDocument, document_id) is None
    assert db.get(ProductDocument, other.id) is other
    assert collection.get()["ids"] == ["other_0"]


def test_delete_failure_keeps_database_record(db, monkeypatch):
    monkeypatch.setattr(api, "ingest_product_document", Mock())
    document = api.create_product_document(1, payload(), db, None)
    collection = Mock()
    collection.delete.side_effect = RuntimeError("Index unavailable")
    monkeypatch.setattr(api, "get_collection", lambda: collection)
    with pytest.raises(HTTPException) as caught:
        api.delete_product_document(1, document.id, db, None)
    assert caught.value.status_code == 503
    assert db.get(ProductDocument, document.id) is document


def test_delete_wrong_product_does_not_touch_index(db, monkeypatch):
    monkeypatch.setattr(api, "ingest_product_document", Mock())
    document = api.create_product_document(1, payload(), db, None)
    get_collection = Mock()
    monkeypatch.setattr(api, "get_collection", get_collection)
    with pytest.raises(HTTPException) as caught:
        api.delete_product_document(999, document.id, db, None)
    assert caught.value.status_code == 404
    get_collection.assert_not_called()


def test_delete_document_without_indexed_chunks(db, monkeypatch):
    monkeypatch.setattr(api, "ingest_product_document", Mock())
    document = api.create_product_document(1, payload(), db, None)
    document_id = document.id
    monkeypatch.setattr(api, "get_collection", Mock(return_value=Mock()))
    api.delete_product_document(1, document_id, db, None)
    assert db.get(ProductDocument, document_id) is None
