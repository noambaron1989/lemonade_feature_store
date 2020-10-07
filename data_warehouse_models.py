import enum

from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User')
    create_time = db.Column(db.DateTime)
    bind_time = db.Column(db.DateTime)
    bindable = db.Column(db.Boolean)


class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User')
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    quote = db.relationship('Quote')


class PaymentType(enum.Enum):
    CREDIT = 'Credit'
    DEBIT = 'Debit'
    PREPAID = 'Prepaid'


class PaymentTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, nullable=False)
    payment_type = db.Column(db.Enum(PaymentType))
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    policy = db.relationship('Policy')
    success = db.Column(db.Boolean)