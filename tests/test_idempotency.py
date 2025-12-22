from decimal import Decimal

from app.db.seed import seed_synthetic_data
from app.db.models import User, Product, Account
from app.services.payments import execute_purchase


def test_idempotent_purchase(db_session):
    seed_synthetic_data(db_session, num_users=1, num_products=1)
    user = db_session.query(User).first()
    product = db_session.query(Product).first()

    acct = db_session.query(Account).filter(Account.user_id == user.id).one()
    acct.balance = Decimal("5000.00")
    db_session.commit()

    idem = "idem_test_12345678"
    tx1 = execute_purchase(db_session, user_id=user.id, product_id=product.id, qty=1, idempotency_key=idem)
    db_session.commit()
    tx2 = execute_purchase(db_session, user_id=user.id, product_id=product.id, qty=1, idempotency_key=idem)
    db_session.commit()

    assert tx1.id == tx2.id
