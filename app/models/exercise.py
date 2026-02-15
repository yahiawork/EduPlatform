
from app.extensions import db

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    level = db.Column(db.String(32))

    require_if = db.Column(db.Boolean, default=False)
    require_else = db.Column(db.Boolean, default=False)
    allow_elif = db.Column(db.Boolean, default=True)

    require_for = db.Column(db.Boolean, default=False)
    require_while = db.Column(db.Boolean, default=False)
    forbid_for = db.Column(db.Boolean, default=False)
    forbid_while = db.Column(db.Boolean, default=False)

    require_function = db.Column(db.Boolean, default=False)
    function_name = db.Column(db.String(64))

    require_print = db.Column(db.Boolean, default=False)
    forbid_print = db.Column(db.Boolean, default=False)
    require_input = db.Column(db.Boolean, default=False)
