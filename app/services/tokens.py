from ..extensions import db
from ..models import User

def add_tokens(user: User, amount: int):
    user.tokens = max(0, (user.tokens or 0) + amount)
    db.session.commit()

def spend_token(user: User, amount: int = 1) -> bool:
    if (user.tokens or 0) < amount:
        return False
    user.tokens -= amount
    db.session.commit()
    return True
