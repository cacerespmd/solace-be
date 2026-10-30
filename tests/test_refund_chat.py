import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.service import generate_ai_response
from app.database import Base
from app.models import Customer, Order, OrderDelivery, PendingSupportAction, SupportTicket


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'refund.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        customer = Customer(name="Buyer", email="buyer@example.com", password_hash="hash")
        session.add(customer)
        session.flush()
        order = Order(customer_id=customer.id, order_number="SOL-3F9A33507B31",
                      status="completed", total_amount=100)
        session.add(order)
        session.flush()
        session.add(OrderDelivery(
            order_id=order.id, recipient_name="Buyer", contact_number="123456789",
            address_line_1="123 Street", barangay="Area", city="City",
            province="Province", postal_code="1234", status="received",
        ))
        session.commit()
        yield session, customer.id, order
    engine.dispose()


def test_specific_refund_issue_creates_ticket_without_extra_questions(db):
    session, customer_id, order = db
    message = f"my order {order.order_number} is not powering on. I want to request a refund."
    result = generate_ai_response(message, session, customer_id)
    ticket = session.scalar(select(SupportTicket))
    assert ticket.category == "refund_request"
    assert ticket.description == message
    assert f"#{ticket.id}" in result["reply"]
    assert "awaiting review" in result["reply"]
    generate_ai_response(message, session, customer_id)
    assert len(session.scalars(select(SupportTicket)).all()) == 1


def test_refund_followup_remembers_order_across_sessions(db):
    session, customer_id, order = db
    first = generate_ai_response(
        f"I want to request a refund for order {order.order_number}.", session, customer_id,
    )
    assert "What went wrong" in first["reply"]
    assert session.scalar(select(SupportTicket)) is None
    # A subsequent HTTP request uses a different database session.
    with Session(session.get_bind()) as followup_session:
        result = generate_ai_response(
            "i tried connecting it to a power outlet and it is not turning on.",
            followup_session, customer_id,
        )
        ticket = followup_session.scalar(select(SupportTicket))
        assert ticket.order_id == order.id
        assert ticket.category == "refund_request"
        assert "power outlet" in ticket.description
        assert f"#{ticket.id}" in result["reply"]
        assert followup_session.get(PendingSupportAction, customer_id) is None


def test_refund_requires_receipt(db):
    session, customer_id, order = db
    order.delivery.status = "delivered"
    session.commit()
    result = generate_ai_response(
        f"I want a refund for {order.order_number} because it is not powering on.",
        session, customer_id,
    )
    assert "confirm receipt" in result["reply"]
    assert session.scalar(select(SupportTicket)) is None


def test_refund_does_not_access_another_customers_order(db):
    session, customer_id, order = db
    result = generate_ai_response(
        f"I want a refund for {order.order_number} because it will not turn on.",
        session, customer_id + 1,
    )
    assert "couldn't find" in result["reply"]
    assert session.scalar(select(SupportTicket)) is None
