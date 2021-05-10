from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
#from flask_bcrypt import Bcrypt
import datetime
import decimal


app = Flask(__name__)
#bcrypt =Bcrypt(app)

ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test_user:123456789andrei@localhost/smarto'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret-key-smarto'

db = SQLAlchemy(app)


##

class Customer(db.Model):
    __tablename__ = 'customer'

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
        #self.password_hash = self.__generate_hash(password)
        self.password_hash = password
        self.created_on = datetime.datetime.now()
        self.details = details

    #def __generate_hash(self, password):
    #    return bcrypt.generate_password_hash(password, rounds=10).decode("utf-8")

    #def check_hash(self, password):
    #    return bcrypt.check_password_hash(self.password, password)
    @staticmethod
    def get_by_email(email):
        return Customer.query.filter_by(email=email)

    @staticmethod
    def get_by_id(id):
        return Customer.query.get(id)


class AccountTypes(db.Model):
    __tablename__ = 'account_types'

    id = db.Column(db.Integer, primary_key=True)
    details = db.Column(db.String(100))

    def __init__(self, details):
        self.details = details


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('account_types.id'), nullable=False)
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
    def get_by_id(account_id):
        return Account.query.get(account_id)

    @staticmethod
    def validate_action(sender_id, type_id, password, amount, receiver_id):
        sender = Account.query.get(sender_id)
        receiver = Account.query.get(receiver_id)
        amount = decimal.Decimal(amount)
        fee = TransactionTypes.query.get(type_id).fee
        if sender and receiver:
            customer = Customer.query.filter_by(id = sender.customer_id).first()
            #if customer.check_hash(password):
            print(customer.password_hash)
            if customer.password_hash == password:
                if sender.balance > (1+fee)*amount:
                    sender.balance -= (1+fee)*amount
                    print("$$$$$$$$$$$$$$> ",amount, (1+fee)*amount)
                    receiver.balance += amount
                    db.session.commit()
                    return {'status' : True, 'message' : 'Success!'}
                else:
                    return {'status' : False, 'message' : 'Insufficient funds'}
        return {'status' : False, 'message' : 'Incorrect credentials'}

class TransactionTypes(db.Model):
    __tablename__ = 'transaction_types'

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
    type_id = db.Column(db.Integer, db.ForeignKey('transaction_types.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Float(8,1), nullable=False)
    details = db.Column(db.String(200))

    def __init__(self, type_id, sender_id, receiver_id, amount, details):
        self.created_on = datetime.datetime.now()
        self.type_id = type_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.amount = amount
        self.details = details

    @staticmethod
    def get_by_id(id):
        return Transaction.query.filter((Transaction.sender_id==id) | (Transaction.receiver_id==id)).order_by(Transaction.created_on.desc()).limit(5).all()

##


@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        data = Transaction.get_by_id(request.form['user_id'])
        users_involved = set()
        users_involved_data = dict()

        for row in data:
            users_involved.add(Account.get_by_id(row.sender_id).customer_id)
            users_involved.add(Account.get_by_id(row.receiver_id).customer_id)

        for u in users_involved:
            users_involved_data[u] = Customer.get_by_id(u).first_name + " " + Customer.get_by_id(u).last_name
        return render_template('index.html', user_id = int(request.form['user_id']), data = data, users_involved_data = users_involved_data)

@app.route('/register/', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        details = request.form['details']

        if len(password) < 8 or len(password) > 36:
            flash('Password must be between 8 and 36 characters long.')
            return redirect(url_for('register'))

        if Customer.get_by_email(email).first():
            flash('User already exists.')
            return redirect(url_for('register'))
        
        else:
            db.session.add(Customer(first_name, last_name, email, password, details))
            db.session.commit()
            return redirect(url_for('index'))

@app.route('/transactions/new/', methods = ['GET', 'POST'])
def add_transaction():
    if request.method == 'GET':
        return render_template('transaction.html')
    else:
        sender_id = request.form['sender_id']
        type_id = request.form['type_id']
        password = request.form['password']
        receiver_id = request.form['receiver_id']
        amount = request.form['amount']
        details = request.form['details']

        response = Account.validate_action(sender_id, type_id, password, amount, receiver_id)

        if response['status']:
            db.session.add(Transaction(type_id, sender_id, receiver_id, amount, details))
            db.session.commit()

        flash(response['message'])
        return render_template('transaction.html')




if __name__ == '__main__':
    app.run()

"""

Assignment.

At Smarto we use Open banking to deduce the financial behavior of clients.
Your task is to:
1. Design a database for open banking (i.e. that should contain at least tables "accounts" for the states of bank accounts and "transactions" for the financial transactions). Fill it with any data (real or fake).
2. Make a REST API endpoint to get 5 last transactions of a user user_id and another endpoint to store a new transaction in the database.
3. Make a webpage that for a given user_id shows the last 5 transactions and for a given transaction inserts it in the database.
4. Bonus: deploy it somewhere (AWS, Heroku, GCP, ...).

"""