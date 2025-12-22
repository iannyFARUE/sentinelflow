from __future__ import annotations

import json
import random
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Account, Product, User


def seed_synthetic_data(db: Session, *, num_users: int = 5, num_products: int = 8) -> dict:
    # Clear existing (dev-friendly). For production you would never do this.
    db.query(Account).delete()
    db.query(Product).delete()
    db.query(User).delete()
    db.commit()

    users: list[User] = []
    for i in range(num_users):
        u = User(
            full_name=f"Test User {i+1}",
            email=f"user{i+1}@example.com",
        )
        users.append(u)
        db.add(u)
    db.flush()

    for u in users:
        # balances between 50 and 2000
        bal = Decimal(str(random.randint(50, 2000))) + Decimal("0.00")
        db.add(Account(user_id=u.id, balance=bal, currency="USD"))

    product_names = [
        ("Laptop Stand", "Ergonomic aluminum stand"),
        ("Mechanical Keyboard", "Tactile switches, backlit"),
        ("Noise Cancelling Headphones", "Over-ear, ANC"),
        ("USB-C Hub", "HDMI + USB + Ethernet"),
        ("Portable SSD 1TB", "Fast external storage"),
        ("Webcam 1080p", "Autofocus webcam"),
        ("Monitor 27-inch", "1440p IPS display"),
        ("Desk Lamp", "Adjustable brightness"),
    ]

    random.shuffle(product_names)
    product_names = product_names[:num_products]

    for name, desc in product_names:
        price = Decimal(str(random.randint(20, 350))) + Decimal("0.99")
        inv = random.randint(1, 30)
        db.add(Product(name=name, description=desc, price=price, currency="USD", inventory_qty=inv, is_active=True))

    db.commit()

    return {
        "users_created": len(users),
        "products_created": len(product_names),
        "note": "Synthetic data seeded",
    }
