from unittest.mock import Mock

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
