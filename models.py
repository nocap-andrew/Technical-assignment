import datetime
import bcrypt
from app import db


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String())
    created_on = db.Column(db.DateTime)
    details = db.Column(db.String(100))

    def __init__(self, first_name, last_name, email, password, details):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = self.__generate_hash(password)
        self.created_on = datetime.datetime.now()
        self.details = details

    def __generate_hash(self, password):
        return bcrypt.generate_password_hash(password, rounds=10).decode("utf-8")

    def check_hash(self, password):
        return bcrypt.check_password_hash(self.password, password)


class AccountTypes(db.Model):
    __tablename__ = 'account_types'

    id = db.Column(db.Integer, primary_key=True)
    details = db.Column(db.String(100))

    def __init__(self, details):
        self.details = details


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.Foreign('customer.id'), nullable=False)
    type_id = db.Column(db.Integer, db.Foreign('account_types.id'), nullable=False)
    created_on = db.Column(db.DateTime)
    balance = db.Column(db.Float(8,1), default=0)
    details = db.Column(db.String(100))

    def __init__(self, customer_id, type_id, details):
        self.customer_id = customer_id
        self.type_id = type_id
        self.created_on = datetime.datetime.now()
        self.balance = 0
        self.details = details

    @staticmethod
    def get_account(account_id):
        return Account.query.get(account_id)

    @staticmethod
    def validate_action(sender_id, password, amount, receiver_id):
        if Account.query.get(sender_id) and Account.query.get(receiver_id):
            customer = Customer.query.filter_by(id = Account.query.get(sender_id).customer_id)
            if customer.check_hash(password):
                if Account.query.get(sender_id).balance > amount:
                    return {'status' : True, 'message' : 'Success!'}
                else:
                    return {'status' : False, 'message' : 'Insufficient funds'}
        return {'status' : False, 'message' : 'Incorrect credentials'}

class TransactionTypes(db.Model):
    __tablename__ = 'account_types'

    id = db.Column(db.Integer, primary_key=True)
    fee = db.Column(db.Float(8,1))
    details = db.Column(db.String(100))

    def __init__(self, fee, details):
        self.fee = fee
        self.details = details

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime)
    sender_id = db.Column(db.Integer, db.Foreign('accounts.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.Foreign('accounts.id'), nullable=False)
    amount = db.Column(db.Float(8,1), nullable=False)
    details = db.Column(db.String(200))

    def __init__(self, sender_id, receiver_id, amount, details):
        self.created_on = datetime.datetime.now()
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.amount = amount
        self.details = details

    @staticmethod
    def get_by_id(id):
        return Transaction.query.filter_by(sender_id=id, receiver_id=id).limit(5).all()




