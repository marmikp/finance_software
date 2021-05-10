import datetime
import time
from operator import itemgetter

import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import session
from database.model import *
import hashlib
import numpy as np

META_DATA = None


def convert_table_to_dict_data(data):
    return {column: getattr(data, column) for column in data.__table__.c.keys()}


def get_amount_value_from_general(username):
    return General.query.filter_by(username=username).first().total_balance


def sum_sub_value_in_balance_amount(amount, operation='sum'):
    total_amount = get_amount_value_from_general(session['username'])
    if operation == 'sum':
        General.query.filter_by(username=session['username']).update({'total_balance': total_amount + amount})
    else:
        General.query.filter_by(username=session['username']).update({'total_balance': total_amount - amount})
    db.session.commit()
    return General.query.filter_by(username=session['username']).first().total_balance


def signup(**kwargs):
    username = kwargs['username']
    password = kwargs['password']
    db.session.add(General(username=username, password=password))
    db.session.commit()


def login(username, password):
    # data = db.session.query.filter_by(username=username, password=password).all()
    password = hashlib.md5(password.encode()).hexdigest()
    data = db.session.query(General).filter(
        and_(General.username == username, General.password == password))
    data_len = len(list(data))
    print(data)
    if data_len > 0:
        return {'code': 200, 'status': "success"}
    else:
        return {'code': 500, 'status': "invalid"}


def get_max_customer_id(id=None):
    if id is None:
        max_query_id = db.session.query(db.func.max(Customer.id))
        max_id = db.session.execute(max_query_id).first()[0]
        if max_id is None:
            return 0
        else:
            return max_id + 1
    else:
        data = Customer.query.filter_by(id=id).first()
        return data


def get_loan_type_by_loan_id(user_id=None, loan_id=None, user_type='loan'):
    if user_type == 'loan':
        entry_table = HaftEntry
    else:
        entry_table = AccountEntry
    return entry_table.query.filter_by(transaction_id=loan_id).first().loan_type


def add_new_customer(user_type="loan", **kwargs):
    try:
        if user_type == "loan":
            if int(kwargs['id']) < get_max_customer_id():
                id = kwargs['id']
                del kwargs['id']
                Customer.query.filter_by(id=int(id)).update(kwargs)
                db.session.commit()
                return {'code': 200, 'status': 'customer details updated'}
            else:
                query = Customer(**kwargs)
                db.session.add(query)
                db.session.commit()
                return {'code': 200, 'status': 'new customer added'}
        else:
            if int(kwargs['id']) < get_max_customer_id():
                id = kwargs['id']
                del kwargs['id']
                Customer.query.filter_by(id=int(id)).update(kwargs)
                db.session.commit()
                return {'code': 200, 'status': 'customer details updated'}
            else:
                query = Customer(**kwargs)
                db.session.add(query)
                db.session.commit()
                return {'code': 200, 'status': 'new customer added'}
    except Exception as e:
        print(e)
        return {'code': 500, 'status': 'server side error occured'}


######## HAFTA #######
def fetch_customers(type="flat"):
    # TODO: code for fetch customers from Customer Table
    pass


def extend_hafta(customer_id, amount, no_of_hafta, loan_id, user_type="loan"):
    # TODO: code to extend hafta
    # get start installment number
    if user_type == "loan":
        entry_table = HaftEntry
    else:
        entry_table = AccountEntry
    no_installments = entry_table.query.filter_by(id=customer_id, transaction_id=loan_id).first().no_installment
    # update installment number of base amount entry
    META_DATA.reflect()
    table = META_DATA.tables[str(customer_id)]
    base_amount_query_data = db.engine.execute(table.select(table.c.emi_amount).where(
        (table.c.loan_id == loan_id) & (table.c.no_of_installment == no_installments)))
    user_data_list = [{column: value for column, value in rowproxy.items()} for rowproxy in base_amount_query_data]
    try:
        db.engine.execute(
            table.update().where(
                (table.c.loan_id == loan_id) & (
                        table.c.no_of_installment == no_installments)).values(
                {"no_of_installment": no_installments + no_of_hafta, "date_to_pay": user_data_list[0]['date_to_pay'] +
                                                                                    relativedelta(months=no_of_hafta)}))
        # add entry of each installment
        for i in range(no_of_hafta):
            add_hafta_track_entry(
                **{'user_id': customer_id, 'loan_id': loan_id, 'emi_amount': amount,
                   'date_to_pay': user_data_list[0]['date_to_pay'] + relativedelta(
                       months=i),
                   'no_of_installment': no_installments + i, 'tx_status': 0})

        entry_table.query.filter_by(id=customer_id, transaction_id=loan_id).update(
            {"last_installment_date": entry_table.query.filter_by(id=customer_id,
                                                                  transaction_id=loan_id).first().last_installment_date + relativedelta(
                months=no_of_hafta),
             "no_installment": no_installments + no_of_hafta})
        db.session.commit()
        return {"code": 200, "status": "hafta extend done"}
    except Exception as e:
        print(e)
        return {"code": 500, "status": "error occurred in hafta extension"}


def add_new_hafta_entry(user_type="loan", **kwargs):
    if user_type == "loan":
        add_query = HaftEntry(**kwargs)
    else:
        add_query = AccountEntry(**kwargs)

    try:
        db.session.add(add_query)
        db.session.commit()

        time.sleep(1)
        if user_type == "loan":
            Customer.query.filter_by(id=add_query.id).update({"customer_type_loan": 1})
        else:
            Customer.query.filter_by(id=add_query.id).update({"customer_type_account": 1})
        create_user_table(kwargs['id'])
        META_DATA.reflect()
        db.session.commit()
        return {'code': 200, 'status': "new hafta entry added", 'transaction_id': add_query.transaction_id}
    except Exception as e:
        print(e)
        return {'code': 500, 'status': "internal server error"}


def add_hafta_track_entry(**data):
    META_DATA.reflect()
    table = META_DATA.tables[str(data['user_id'])]
    db.engine.execute(table.insert(), **data)


def add_installment(installment_num=0, paid_date=datetime.now(), user_type="loan", **kwargs):
    table = META_DATA.tables[str(kwargs['id'])]
    try:
        loan_type = get_loan_type_by_loan_id(loan_id=kwargs['transaction_id'])
        user_data_tx_status = db.engine.execute(table.select().where(
            (table.c.loan_id == kwargs['transaction_id']) & (table.c.no_of_installment == installment_num)))
        user_data_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_data_tx_status]
        tx_status = user_data_list[0]['tx_status']
        if tx_status:
            total_balance = General.query.filter_by(username=session.get('username')).first().total_balance
            if user_type == "loan":
                General.query.filter_by(username=session.get('username')).update(
                    {'total_balance': total_balance - user_data_list[0]['paid_amount']})
            else:
                General.query.filter_by(username=session.get('username')).update(
                    {'total_balance': total_balance + user_data_list[0]['paid_amount']})
            db.session.commit()
            user_d_next = db.engine.execute(table.select().where(
                (table.c.loan_id == kwargs['transaction_id']) & (table.c.tx_status == 0)).order_by(
                table.c.no_of_installment))
            user_data_list_next = [{column: value for column, value in rowproxy.items()} for rowproxy in user_d_next]
            user_d_current = db.engine.execute(table.select().where(
                (table.c.loan_id == kwargs['transaction_id']) & (table.c.no_of_installment == installment_num)))
            user_data_list_current = [{column: value for column, value in rowproxy.items()} for rowproxy in
                                      user_d_current]

            amount_diff = kwargs['emi_amount'] - user_data_list_current[0]['paid_amount']
            db.engine.execute(table.update().where(
                (table.c.loan_id == kwargs['transaction_id']) & (
                            table.c.no_of_installment == user_data_list_next[0]['no_of_installment'])).values(
                {'emi_amount': user_data_list_next[0]['emi_amount'] - amount_diff}))
            if user_type == 'loan':
                if loan_type == 'flat':
                    if installment_num + 1 != HaftEntry.query.filter_by(
                            transaction_id=kwargs['transaction_id']).first().no_installment:
                        current_pending_interest = General.query.filter_by(
                            username=session.get('username')).first().total_interest_pending
                        current_earned_interest = General.query.filter_by(
                            username=session.get('username')).first().total_interest_earned
                        next_pending_interest = current_pending_interest + user_data_list_current[0]['paid_amount']
                        General.query.filter_by(username=session.get('username')).update(
                            {'total_interest_pending': next_pending_interest,
                             'total_interest_earned': current_earned_interest - user_data_list_current[0][
                                 'paid_amount']})
                else:
                    user_loan_details = HaftEntry.query.filter_by(transaction_id=kwargs['transaction_id']).first()
                    each_month_interest = user_loan_details.interest / user_loan_details.no_installment
                    current_pending_interest = General.query.filter_by(
                        username=session.get('username')).first().total_interest_pending
                    current_earned_interest = General.query.filter_by(
                        username=session.get('username')).first().total_interest_earned
                    next_pending_interest = current_pending_interest + each_month_interest
                    General.query.filter_by(username=session.get('username')).update(
                        {'total_interest_pending': next_pending_interest,
                         'total_interest_earned': current_earned_interest - each_month_interest})
                db.session.commit()

        db.engine.execute(
            table.update().where(
                (table.c.loan_id == kwargs['transaction_id']) & (table.c.no_of_installment == installment_num)).values(
                {'paid_amount': kwargs['paid_amount'], 'paid_date': paid_date, 'tx_status': 1}))
        if user_type == 'loan':
            sum_sub_value_in_balance_amount(kwargs['paid_amount'], 'sum')
        else:
            sum_sub_value_in_balance_amount(kwargs['paid_amount'], 'sub')
        if kwargs['emi_amount'] != kwargs['paid_amount']:
            user_d = db.engine.execute(table.select().where(
                (table.c.loan_id == kwargs['transaction_id']) & (table.c.tx_status == 0)).order_by(
                table.c.no_of_installment))
            user_data_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_d]
            update_row_installment_no = user_data_list[0]['no_of_installment']
            if len(user_data_list):
                db.engine.execute(
                    table.update().where(
                        (table.c.loan_id == kwargs['transaction_id']) & (
                                table.c.no_of_installment == update_row_installment_no)).values(
                        {'emi_amount': user_data_list[0]['emi_amount'] + (
                                kwargs['emi_amount'] - kwargs['paid_amount'])}))

        user_data_tx_status = db.engine.execute(table.select().where(
            (table.c.loan_id == kwargs['transaction_id']) & (table.c.tx_status == 0)))
        user_data_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_data_tx_status]
        if len(user_data_list) == 0:
            if user_type == "loan":
                HaftEntry.query.filter_by(transaction_id=kwargs['transaction_id']).update({'loan_status': 1})
            else:
                AccountEntry.query.filter_by(transaction_id=kwargs['transaction_id']).update({'loan_status': 1})

            db.session.commit()
        if user_type == 'loan':
            if loan_type == 'flat':
                if installment_num + 1 != HaftEntry.query.filter_by(
                        transaction_id=kwargs['transaction_id']).first().no_installment:
                    current_pending_interest = General.query.filter_by(
                        username=session.get('username')).first().total_interest_pending
                    current_earned_interest = General.query.filter_by(
                        username=session.get('username')).first().total_interest_earned
                    next_pending_interest = current_pending_interest - kwargs['paid_amount']
                    General.query.filter_by(username=session.get('username')).update(
                        {'total_interest_pending': next_pending_interest,
                         'total_interest_earned': current_earned_interest + kwargs['paid_amount']})
            else:
                user_loan_details = HaftEntry.query.filter_by(transaction_id=kwargs['transaction_id']).first()
                each_month_interest = user_loan_details.interest / user_loan_details.no_installment
                current_pending_interest = General.query.filter_by(
                    username=session.get('username')).first().total_interest_pending
                current_earned_interest = General.query.filter_by(
                    username=session.get('username')).first().total_interest_earned
                next_pending_interest = current_pending_interest - each_month_interest
                General.query.filter_by(username=session.get('username')).update(
                    {'total_interest_pending': next_pending_interest,
                     'total_interest_earned': current_earned_interest + min(kwargs['paid_amount'], each_month_interest)})

            db.session.commit()
            total_balance = General.query.filter_by(username=session.get('username')).first().total_balance
            tx_hist_query = TransactionHistory(party_id=kwargs['id'], loan_id=kwargs['transaction_id'],
                                               account_type='loan emi',
                                               amount=kwargs['paid_amount'],
                                               status='cr', total_balance=total_balance)
            db.session.add(tx_hist_query)
            db.session.commit()

        return {"code": 200, "status": "installment updated successfully"}
    except Exception as e:
        print(e)
        return {"code": 500, "status": "error in installment update"}


def get_user_data(id=None, loan_type="hafta", user_type='loan'):
    if id is not None:
        user_table = META_DATA.tables[str(id)]
        if user_type == 'loan':
            entry_table = HaftEntry
        else:
            entry_table = AccountEntry
        if loan_type == "hafta":
            user_data = []
            user_active_loans = [val.transaction_id for val in entry_table.query.filter_by(id=id, loan_status=0).all()]
            for loan in user_active_loans:
                user_d = db.engine.execute(
                    user_table.select().where(user_table.c.loan_id == loan).order_by(user_table.c.tx_status.desc()))
                user_d_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_d]
                if user_type != 'loan':
                    for val in user_d_list:
                        val['remark'] = entry_table.query.filter_by(id=id, transaction_id=loan).first().remark
                user_data += user_d_list
            user_data = sorted(user_data, key=itemgetter('tx_status'))

            print(user_data)
            return user_data
    else:
        return {"code": 500, "status": "user id is not available"}


def get_user_id_from_loan_id(loan_id, loan_type='hafta'):
    if loan_type == "hafta":
        entry_table = HaftEntry
    else:
        entry_table = AccountEntry
    return entry_table.query.filter_by(transaction_id=loan_id).first().id


def get_user_data_by_loan_id(loan_id=None, loan_type="hafta", user_type='loan'):
    if id is not None:

        if user_type == 'loan':
            entry_table = HaftEntry
        else:
            entry_table = AccountEntry
        if loan_type == "hafta":
            user_data = []
            user_id = get_user_id_from_loan_id(loan_id)
            user_table = META_DATA.tables[str(user_id)]
            user_d = db.engine.execute(
                user_table.select().where(user_table.c.loan_id == loan_id).order_by(user_table.c.tx_status.desc()))
            user_d_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_d]
            user_data += user_d_list
            user_data = sorted(user_data, key=itemgetter('tx_status'))
            print(user_data)
            return user_data
    else:
        return {"code": 500, "status": "user id is not available"}


def get_user_info_by_id(user_id=None, return_type="object", user_type='loan'):
    if user_type == 'loan':
        entry_table = HaftEntry
    else:
        entry_table = AccountEntry
    if user_id is not None:
        data = Customer.query.filter_by(id=user_id).all()
        if return_type == "object":
            return data
        else:
            for i, d in enumerate(data):
                data[i] = convert_table_to_dict_data(d)
                loans = []
                for val in entry_table.query.filter_by(id=user_id, loan_status=0).all():
                    loans.append(val.transaction_id)
                data[i]['loans'] = loans
            return data


def get_pending_installment_of_loan_id(user_id, loan_id):
    user_table = META_DATA.tables[str(user_id)]
    data = db.engine.execute(user_table.select().where(
        (user_table.c.loan_id == loan_id) & (user_table.c.user_id == user_id) & (user_table.c.tx_status == 0)))
    user_d_list = [{column: value for column, value in rowproxy.items()} for rowproxy in data]
    return user_d_list


def get_users_details(loan_type="both", user_type="loan", all_entries=False):
    if user_type == 'loan':
        if all_entries:
            customer_data = Customer.query.all()
        else:
            customer_data = Customer.query.filter_by(customer_type_loan=1).all()
    elif user_type == 'account':
        if all_entries:
            customer_data = Customer.query.all()
        else:
            customer_data = Customer.query.filter_by(customer_type_account=1).all()
    elif user_type == 'debit':
        if all_entries:
            customer_data = Customer.query.all()
        else:
            customer_data = Customer.query.filter_by(customer_type_crdr=1).all()
    else:
        customer_data = Customer.query.all()
    for i, data in enumerate(customer_data):
        data = convert_table_to_dict_data(data)
        data['num_loan_account'], data['num_loan_hafta'] = 0, 0
        if data['customer_type_account']:
            if all_entries:
                data['num_loan_account'] = len(AccountEntry.query.filter_by(id=data['id']).all())
            else:
                data['num_loan_account'] = len(AccountEntry.query.filter_by(id=data['id'], loan_status=0).all())
            data['customer_type'] = "account"
            pass
        if data['customer_type_loan']:
            if all_entries:
                loan_data = HaftEntry.query.filter_by(id=data['id']).all()
            else:
                loan_data = HaftEntry.query.filter_by(id=data['id'], loan_status=0).all()
            data['num_loan_hafta'] = len(loan_data)
            data['customer_type'] = "loan"
        if data['customer_type_account'] and data['customer_type_loan']:
            data['customer_type'] = "both"
        customer_data[i] = data
    return customer_data


def get_user_loan_entries_by_user_id(user_id, only_active=True, user_type="loan"):
    if user_type == "loan":
        entry_table = HaftEntry
    else:
        entry_table = AccountEntry
    if only_active:
        data = entry_table.query.filter_by(id=user_id, loan_status=0).all()
    else:
        data = entry_table.query.filter_by(id=user_id).all()

    data = [convert_table_to_dict_data(d) for d in data]
    return data


######## PERSONAL ACCOUNT #####
def add_new_account_entry(**kwargs):
    # TODO: add new account entry
    pass


def pay_account_installment(**kwargs):
    # TODO: code to add paid installment entry
    pass


######## REPORT #########
def fetch_pending_installment(datefrom, dateto, type="both"):
    # TODO: fetch all the entry of pending customers between defined dates
    pass


def party_to_party_transactions_report(**kwargs):
    # TODO: code to fetch party to party transactions
    pass


def fetch_account_transaction(date=None):
    # TODO: code to fetch all the entry of account filter by date if available else fetch all entries
    pass


def close_loan(user_id, loan_id, amount, user_type="loan"):
    # add amount in user_table as next installment
    # mark all tx_status as 1
    # change loan status in haftentry table
    if user_type == "loan":
        entry_table = HaftEntry
    else:
        entry_table = AccountEntry
    # try:
    table = META_DATA.tables[str(user_id)]
    installment_data = db.engine.execute(table.select(table.c.no_of_installment).where(
        (table.c.loan_id == loan_id) * (table.c.tx_status == 0)).order_by(table.c.no_of_installment.asc()))
    user_data_list = [{column: value for column, value in rowproxy.items()} for rowproxy in installment_data]
    latest_installment_no = user_data_list[0]['no_of_installment']
    db.engine.execute(
        table.update().where(
            (table.c.loan_id == loan_id) & (
                    table.c.no_of_installment == latest_installment_no)).values(
            {'paid_amount': amount, 'paid_date': datetime.now().date(), 'tx_status': 1}))
    for d in user_data_list:
        db.engine.execute(
            table.update().where(
                (table.c.loan_id == loan_id) & (
                        table.c.no_of_installment == d['no_of_installment'])).values(
                {'paid_amount': 0, 'paid_date': datetime.now().date(), 'tx_status': 1}))

    entry_table.query.filter_by(id=user_id, transaction_id=loan_id).update({'loan_status': 1})
    db.session.commit()
    if user_type == 'loan':
        sum_sub_value_in_balance_amount(amount, 'sum')
    else:
        sum_sub_value_in_balance_amount(amount, 'sub')

    return {'code': 200, 'status': 'loan closed successfully'}
    # except Exception as e:
    #     print(e)
    #     return {"code": 500, "status": "some error occured during closing the loan"}


def get_pending_installments_of_user(user_id, date):
    META_DATA.reflect()
    user_table = META_DATA.tables[str(user_id)]
    # select pending values and payment
    emis = db.engine.execute(user_table.select(user_table.c.emi_amount).where(
        (user_table.c.date_to_pay <= date) &
        (user_table.c.tx_status == 0)))
    emis_count = db.engine.execute(user_table.select(user_table.c.emi_amount).where(
        user_table.c.tx_status == 0))
    emis_dict = [{column: value for column, value in rowproxy.items()} for rowproxy in emis]
    emis_dict_count = [{column: value for column, value in rowproxy.items()} for rowproxy in emis_count]
    loan_id_dict = {}
    for val in emis_dict:
        if val['loan_id'] not in list(loan_id_dict.keys()):
            loan_id_dict[val['loan_id']] = [0, 0, 0, 0]
        loan_id_dict[val['loan_id']][0] += val['emi_amount']
        loan_id_dict[val['loan_id']][1] += 1
        loan_id_dict[val['loan_id']][2] = val['date_to_pay']
        loan_id_dict[val['loan_id']][3] = len(emis_dict_count)
    return loan_id_dict, emis_dict


def get_user_entries_between_date(user_id, from_date, to_date):
    META_DATA.reflect()
    user_table = META_DATA.tables[str(user_id)]
    user_entries = db.engine.execute(user_table.select().where(
        (user_table.c.paid_date >= from_date) & (user_table.c.paid_date <= to_date) & (user_table.c.tx_status == 1)))
    user_entries = [{column: value for column, value in rowproxy.items()} for rowproxy in user_entries]
    return user_entries


def get_day_wise_installments(date, user_type='loan'):
    columns = ['User ID', 'Loan ID', 'No of Installment', 'EMI Date', 'Paid Date', 'Paid Amount']
    entry_list_df = pd.DataFrame(columns=columns)
    user_data_list = Customer.query.all()
    for data in user_data_list:
        data_dict = convert_table_to_dict_data(data)
        META_DATA.reflect()
        try:
            user_entry_table = META_DATA.tables[str(data_dict['id'])]
            user_entries = db.engine.execute(user_entry_table.select().where(user_entry_table.c.paid_date == date))
            user_entries = [{column: value for column, value in rowproxy.items()} for rowproxy in user_entries]
            for entry in user_entries:
                row = pd.Series([data_dict['id'], entry['loan_id'], entry['no_of_installment'], entry['date_to_pay'],
                                 entry['paid_date'], entry['paid_amount']], columns)
                entry_list_df = entry_list_df.append(row, ignore_index=True)
        except Exception as e:
            print(e)
            continue

    return entry_list_df, entry_list_df['Paid Amount'].sum()


def get_index_form_data_total():
    active_customer = db.session.query(Customer).filter(
        or_(Customer.customer_type_loan == 1, Customer.customer_type_account == 1, Customer.customer_type_crdr == 1))
    total_customer = len(list(active_customer))
    active_customer = db.session.query(Customer).filter(Customer.customer_type_loan == 1)
    loan_customer = len(list(active_customer))
    active_customer = db.session.query(Customer).filter(Customer.customer_type_account == 1)
    account_customer = len(list(active_customer))
    active_customer = db.session.query(Customer).filter(Customer.customer_type_crdr == 1)
    debit_accounts = len(list(active_customer))
    total_balance_output = General.query.filter_by(username=session.get('username')).first()
    total_balance = "{:.2f}".format(total_balance_output.total_balance)
    total_interest_pending = "{:.2f}".format(total_balance_output.total_interest_pending)
    total_interest_earned = "{:.2f}".format(total_balance_output.total_interest_earned)
    return {'total_customer': total_customer, 'loan_customer': loan_customer, 'account_customer': account_customer,
            'debit_accounts': debit_accounts, 'total_balance': total_balance, 'total_interest_pending':
                total_interest_pending, 'total_interest_earned': total_interest_earned}


def finance_user_details():
    general_details = General.query.filter_by(username=session.get('username')).first()
    general_details = convert_table_to_dict_data(general_details)
    del general_details['password']
    del general_details['username']
    return general_details


def update_finance_user(**kwargs):
    try:
        General.query.filter_by(username=session.get('username')).update(kwargs)
        db.session.commit()
        return {'code': 200, 'status': 'data updated successfully'}
    except Exception as e:
        print(e)
        return {'code': 500, 'status': 'server side error occured'}


def get_total_pending_amount():
    total_active_loans = Customer.query.filter_by(customer_type_loan=1).all()
    total_pending_amount = 0
    for loan in total_active_loans:
        table = META_DATA.tables[str(loan.id)]
        pending_transactions = db.engine.execute(table.select().where(table.c.tx_status == 0))
        pending_transactions_list = [{column: value for column, value in rowproxy.items()} for rowproxy in
                                     pending_transactions]
        for transaction in pending_transactions_list:
            total_pending_amount += transaction['emi_amount']

    return total_pending_amount


def get_guarantor_details_by_loan_id(user_id, loan_id):
    data = convert_table_to_dict_data(HaftEntry.query.filter_by(id=user_id, transaction_id=loan_id).first())

    return data


def update_guarantor_details(user_id, loan_id, data_query):
    try:
        HaftEntry.query.filter_by(id=user_id, transaction_id=loan_id).update(data_query)
        db.session.commit()
        return {'code': 200, 'status': 'update success'}
    except Exception as e:
        print(e)
        return {'code': 500, 'status': 'server side error occured in guarantor update'}


def get_daily_report_by_date(date):
    day_transactions = TransactionHistory.query.filter_by(tx_date=date).all()
    for i, d in enumerate(day_transactions):
        name = Customer.query.filter_by(id=d.party_id).first().user_name
        day_transactions[i] = convert_table_to_dict_data(d)
        day_transactions[i]['name'] = name
    day_transactions = pd.DataFrame.from_dict(day_transactions)
    return day_transactions


def get_user_pending_amount(user_id, account_type='loan'):
    entry_table = META_DATA.tables[str(user_id)]
    pending_entries = db.engine.execute(entry_table.select().where(
        (entry_table.c.user_id == user_id) & (entry_table.c.tx_status == 0)))
    pending_entries = [{column: value for column, value in rowproxy.items()} for rowproxy in pending_entries]
    total_amount = 0
    for val in pending_entries:
        total_amount += val['emi_amount']
    if account_type != 'account':
        total_amount *= -1
    return total_amount


def get_general_report():
    general_data = General.query.filter_by(username=session.get('username')).first()
    all_user_data = {}
    hafta_entry_users = HaftEntry.query.filter_by(loan_status=0).all()
    for user_data in hafta_entry_users:
        all_user_data[Customer.query.filter_by(id=user_data.id).first().user_name] = get_user_pending_amount(user_data.id)

    hafta_entry_users = AccountEntry.query.filter_by(loan_status=0).all()
    for user_data in hafta_entry_users:
        all_user_data[Customer.query.filter_by(id=user_data.id).first().user_name] = get_user_pending_amount(
            user_data.id, account_type='account')

    customer_entries = Customer.query.filter_by(customer_type_crdr=1).all()
    for entry in customer_entries:
        customer_data = CrDrEntry.query.filter_by(id=entry.id).all()
        amount = 0
        for data in customer_data:
            amount -= data.base_amount
        all_user_data[Customer.query.filter_by(id=entry.id).first().user_name] = amount

    df_dict = {'name': list(all_user_data.keys()), 'value': list(all_user_data.values())}
    df_dict['name'].append('Total')
    df_dict['value'].append(np.array(df_dict['value']).sum())

    user_data_df = pd.DataFrame.from_dict(df_dict)
    general_table_dict = {'name': ['Total Available Balance', 'Total Pending Balance', 'Total Earned Interest',
                                   'Total Pending Interest', 'Total Interest'],
                          'value': [general_data.total_balance, get_total_pending_amount(),
                                    general_data.total_interest_earned, general_data.total_interest_pending,
                                    general_data.total_interest_pending+general_data.total_interest_earned]}
    return {'general': pd.DataFrame.from_dict(general_table_dict).to_html(index=False, header=False), 'all_transaction':
        user_data_df.to_html(index=False, header=False)}
