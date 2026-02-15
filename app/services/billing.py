from datetime import datetime
from ..extensions import db
from ..models import User, Role

def disable_expired_accounts():
    now = datetime.utcnow()
    users = User.query.filter(User.role.in_([Role.TEACHER, Role.STUDENT])).all()
    changed = 0
    for u in users:
        if u.paid_until and u.paid_until < now:
            if u.is_active_paid:
                u.is_active_paid = False
                changed += 1
    if changed:
        db.session.commit()
    return changed
