import datetime
import random
from faker import Faker
from data_warehouse_models import db, User, Quote, Policy, PaymentTransaction, PaymentType

'''
A script to create the database and fake data.
'''

NUM_USERS = 1000
NUM_QUOTES = 2000
NUM_POLICIES = 500
NUM_PAYMENT_TRANSACTIONS = 500

fake = Faker()


def insert_user():
    user = User()
    user.name = fake.name()
    db.session.add(user)
    return user


def insert_quote(user: User):
    quote = Quote()
    quote.user_id = user.id if user else None
    quote.user = user
    quote.create_time = fake.date_time_between(start_date="-1y", end_date="now", tzinfo=None)
    if user:
        quote.bindable = True
        quote.bind_time = quote.create_time + datetime.timedelta(seconds=random.randint(0, 1800))
    db.session.add(quote)
    return quote


def insert_policy(quote: Quote):
    policy = Policy()
    policy.user_id = quote.user.id
    policy.user = quote.user
    policy.quote_id = quote.id
    policy.quote = quote
    db.session.add(policy)
    return policy


def insert_payment_transaction(policy: Policy):
    payment_transaction = PaymentTransaction()
    payment_transaction.policy_id = policy.id
    payment_transaction.policy = policy
    payment_transaction.payment_type = random.choice(list(PaymentType))
    payment_transaction.success = bool(random.randint(0, 5))
    payment_transaction.time = policy.quote.bind_time + datetime.timedelta(seconds=random.randint(0, 1800))
    db.session.add(payment_transaction)
    return payment_transaction


if __name__ == "__main__":
    db.create_all()

    users = [insert_user() for _ in range(NUM_USERS)]
    db.session.commit()

    quotes = [insert_quote(random.choice(users)) for _ in range(NUM_QUOTES) if random.randint(0, 2)]
    db.session.commit()

    quotes_without_user = [insert_quote(None) for _ in range(NUM_QUOTES - len(quotes))]
    db.session.commit()

    policies = [insert_policy(random.choice(quotes)) for _ in range(NUM_POLICIES)]
    db.session.commit()

    payment_transactions = [insert_payment_transaction(policy) for policy in policies]
    db.session.commit()
