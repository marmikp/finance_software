from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, MetaData, Table
from sqlalchemy.sql.ddl import CreateTable

import config

db = SQLAlchemy()


def init_database(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config.db_name}.dll?check_same_thread=False'
    with app.test_request_context():
        db.init_app(app)
        db.create_all()


def create_user_table(table_name):
    TABLE_SPEC = [
        (('id', db.Integer), {'primary_key': True, 'autoincrement': True}),
        (('user_id', db.Integer, ForeignKey(Customer.id)), {}),
        (('loan_id', db.Integer, ForeignKey(HaftEntry.transaction_id)), {}),
        (('emi_amount', db.Float), {}),
        (('date_to_pay', db.DateTime), {}),
        (('no_of_installment', db.Integer), {}),
        (('paid_amount', db.Float), {}),
        (('paid_date', db.DateTime), {}),
        (('tx_status', db.Integer), {'default': 0}),
        (('party_to_party_transaction', db.Integer), {'default': 0}),
        (('party_to_party_transaction_amount', db.Float), {'default': 0}),
        (('party_to_party_transaction_with', db.Integer), {'default': 0}),
        (('total_transaction_amount_pending', db.Float), {'default': 0}),
        (('tx_hist_id', db.Integer), {})
    ]
    try:
        columns = []
        for args, kwargs in TABLE_SPEC:
            columns.append(db.Column(*args, **kwargs))
        table = Table(table_name, MetaData(), *columns)
        table_creation_sql = CreateTable(table)
        db.session.execute(table_creation_sql)
        db.session.commit()

        return {'code': 200, 'status': 'table created successfully'}
    except Exception as e:
        print(e)
        return {'code': 500, 'status': 'error in table creation'}


def create_account_user_table(table_name):
    TABLE_SPEC = [
        (('id', db.Integer), {'primary_key': True, 'autoincrement': True}),
        (('user_id', db.Integer, ForeignKey(Customer.id)), {}),
        (('tx_id', db.Integer, ForeignKey(AccountEntry.transaction_id)), {}),
        (('amount', db.Float), {}),
        (('date', db.DateTime), {}),
        (('tx_type', db.Integer), {}),
        (('remark', db.String(500)), {})
        ]
    try:
        columns = []
        for args, kwargs in TABLE_SPEC:
            columns.append(db.Column(*args, **kwargs))
        table = Table(table_name, MetaData(), *columns)
        table_creation_sql = CreateTable(table)
        db.session.execute(table_creation_sql)
        db.session.commit()

        return {'code': 200, 'status': 'table created successfully'}
    except Exception as e:
        print(e)
        return {'code': 500, 'status': 'error in table creation'}


class Customer(db.Model):
    __tablename__ = 'customer'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(50), index=True, nullable=False)
    user_alias = db.Column(db.String(5), index=True, nullable=True)
    user_address = db.Column(db.String(50), index=True, nullable=False)
    user_phone = db.Column(db.Integer, index=True, nullable=False)
    user_phone_2 = db.Column(db.Integer, index=True, nullable=True)
    user_city = db.Column(db.String(10), index=True, nullable=False)
    customer_type_loan = db.Column(db.Integer, index=True, nullable=False, default=0)
    customer_type_account = db.Column(db.Integer, index=True, nullable=False, default=0)
    customer_type_crdr = db.Column(db.Integer, index=True, nullable=False, default=0)

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.client_id

    def __repr__(self):
        return str({"id": self.id, "user_name": self.user_name, "user_alias": self.user_alias,
                    "user_address": self.user_address, "user_phone": self.user_phone, "user_city": self.user_city,
                    'customer_type_crdr': self.customer_type_crdr})


class CrDrEntry(db.Model):
    __tablename__ = "crdr_entries"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, ForeignKey(Customer.id))
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_amount = db.Column(db.Float, index=True, nullable=False)
    paid_date = db.Column(db.Date, index=True, default=datetime.now().date())
    remark = db.Column(db.String(500), index=False, nullable=True)

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.client_id

    def __repr__(self):
        return str({"id": self.id, "transaction_id": self.transaction_id, "base_amount": self.base_amount,
                    "paid_date": self.paid_date, "remark": self.remark})

class HaftEntry(db.Model):
    __tablename__ = 'hafta_entry'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, ForeignKey(Customer.id))
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_amount = db.Column(db.Float, index=True, nullable=False)
    interest = db.Column(db.Float, index=True, nullable=False)
    total_amount = db.Column(db.Float, index=True, nullable=False)
    no_installment = db.Column(db.Integer, index=True, nullable=False)
    start_date = db.Column(db.DateTime, index=True, nullable=True)
    installment_period = db.Column(db.String(10), index=False, nullable=True, default="Monthly")
    loan_type = db.Column(db.String(5), index=True, nullable=False, default="flat")
    last_installment_date = db.Column(db.DateTime, index=True, nullable=False)
    loan_status = db.Column(db.Integer, index=True, nullable=False, default=0)
    guarantor_1_name = db.Column(db.String(50), index=True, nullable=True)
    guarantor_2_name = db.Column(db.String(50), index=True, nullable=True)
    guarantor_1_phone = db.Column(db.Integer, index=True, nullable=True)
    guarantor_2_phone = db.Column(db.Integer, index=True, nullable=True)
    guarantor_1_address = db.Column(db.String(50), index=True, nullable=True)
    guarantor_2_address = db.Column(db.String(50), index=True, nullable=True)
    remark = db.Column(db.String(500), index=True, nullable=True, default='')

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.client_id

    def __repr__(self):
        return str({"id": self.id, "transaction_id": self.transaction_id, "base_amount": self.base_amount,
                    "interest": self.interest, "total_amount": self.total_amount, "no_installment": self.no_installment,
                    "start_date": self.start_date, "installment_period": self.installment_period,
                    "loan_type": self.loan_type, "last_installment_date": self.last_installment_date,
                    "loan_status": self.loan_status, "guarantor_1_name": self.guarantor_1_name,
                    "guarantor_2_name ": self.guarantor_2_name, "guarantor_1_phone": self.guarantor_1_phone,
                    "guarantor_2_phone": self.guarantor_2_phone, "guarantor_1_address": self.guarantor_1_address,
                    "guarantor_2_address": self.guarantor_2_address})


class AccountEntry(db.Model):
    __tablename__ = 'account_entry'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, ForeignKey(Customer.id))
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_amount = db.Column(db.Float, index=True, nullable=False)
    interest = db.Column(db.Float, index=True, nullable=False)
    total_amount = db.Column(db.Float, index=True, nullable=False)
    no_installment = db.Column(db.Integer, index=True, nullable=False)
    start_date = db.Column(db.DateTime, index=True, nullable=True)
    installment_period = db.Column(db.String(10), index=False, nullable=True, default="Monthly")
    loan_type = db.Column(db.String(5), index=True, nullable=False, default="flat")
    last_installment_date = db.Column(db.DateTime, index=True, nullable=False)
    loan_status = db.Column(db.Integer, index=True, nullable=False, default=0)
    remark = db.Column(db.String(500), index=True, nullable=True, default='')

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.client_id

    def __repr__(self):
        return str({"id": self.id, "transaction_id": self.transaction_id, "base_amount": self.base_amount,
                    "interest": self.interest, "total_amount": self.total_amount, "no_installment": self.no_installment,
                    "start_date": self.start_date, "installment_period": self.installment_period,
                    "loan_type": self.loan_type, "last_installment_date": self.last_installment_date,
                    "loan_status": self.loan_status})


class General(db.Model):
    __tablename__ = 'general'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, index=True, nullable=False)
    password = db.Column(db.String(50), index=True, nullable=False)
    total_balance = db.Column(db.Integer, index=True, nullable=False, default=0)
    total_interest_earned = db.Column(db.Integer, index=True, nullable=False, default=0)
    total_interest_pending = db.Column(db.Integer, index=True, nullable=False, default=0)
    total_base_amount_pending = db.Column(db.Integer, index=True, nullable=False, default=0)
    total_available_balance = db.Column(db.Integer, index=True, nullable=False, default=0)
    interest_rate = db.Column(db.Float, index=True, nullable=False, default=0)
    email = db.Column(db.String(50), index=True, nullable=False, default=0)
    phone = db.Column(db.Integer, index=True, nullable=False, default=0)
    name = db.Column(db.String(50), index=True, nullable=False, default=0)

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.client_id

    def __repr__(self):
        return str({"id": self.id, "username": self.username,
                    "password": self.password,
                    "total_balance": self.total_balance,
                    "total_interest_earned": self.total_interest_earned,
                    "total_interest_pending": self.total_interest_pending,
                    "total_base_amount_pending": self.total_base_amount_pending,
                    "total_available_balance": self.total_available_balance,
                    "interest_rate": self.interest_rate})


class TransactionHistory(db.Model):
    __tablename__ = 'transaction_history'
    __table_args__ = {'extend_existing': True}
    tx_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    party_id = db.Column(db.Integer, ForeignKey(Customer.id))
    loan_id = db.Column(db.Integer, nullable=True)
    account_type = db.Column(db.String(10), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(5), nullable=True)
    total_balance = db.Column(db.Float, nullable=True)
    tx_date = db.Column(db.Date, nullable=False, default=datetime.now().date())


    def get_id(self):
        return self.tx_id

    def __unicode__(self):
        return self.client_id

    def __repr__(self):
        return str({"tx_id": self.tx_id,"party_id": self.party_id, "loan_id": self.loan_id,
                    "account_type": self.account_type, "amount": self.amount, "status": self.status,
                    "total_balance": self.total_balance, "tx_date": self.tx_date })