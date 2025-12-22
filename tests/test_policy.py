from decimal import Decimal

from app.agent.planner import simple_planner
from app.agent.policy import evaluate_plan
from app.db.seed import seed_synthetic_data
from app.db.models import User, Product, Account


def test_purchase_requires_confirmation(db_session):
    seed_synthetic_data(db_session, num_users=1, num_products=1)
    user = db_session.query(User).first()
    product = db_session.query(Product).first()

    # Make sure user has money
    acct = db_session.query(Account).filter(Account.user_id == user.id).one()
    acct.balance = Decimal("5000.00")
    db_session.commit()

    plan = simple_planner(f"buy product_id={product.id} qty=1", user_id=user.id)
    decision = evaluate_plan(db_session, plan, user_id=user.id)

    assert decision.allowed is True
    assert decision.needs_confirmation is True
    assert "Confirm purchase" in (decision.confirmation_summary or "")
