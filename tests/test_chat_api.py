from decimal import Decimal

from app.db.seed import seed_synthetic_data
from app.db.models import User, Product, Account


def test_chat_balance_flow(client, db_session):
    seed_synthetic_data(db_session, num_users=1, num_products=1)
    user = db_session.query(User).first()

    resp = client.post("/chat", json={"session_id": "s1", "user_id": user.id, "message": "what is my balance"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Your balance is" in data["message"]


def test_chat_purchase_requires_confirmation(client, db_session):
    seed_synthetic_data(db_session, num_users=1, num_products=1)
    user = db_session.query(User).first()
    product = db_session.query(Product).first()

    acct = db_session.query(Account).filter(Account.user_id == user.id).one()
    acct.balance = Decimal("5000.00")
    db_session.commit()

    resp = client.post("/chat", json={"session_id": "s2", "user_id": user.id, "message": f"buy product_id={product.id} qty=1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_confirmation"] is True
    assert data["confirmation_token"] is not None
    assert "confirm" in data["message"].lower()
