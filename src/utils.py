from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import session

from database import db_utils
from database.db_utils import get_pending_installment_of_loan_id, convert_table_to_dict_data, \
    get_pending_installments_of_user, get_user_pending_amount, get_user_due_amount
from database.model import db, HaftEntry, CrDrEntry, AccountEntry, Customer, General, TransactionHistory

calculate_emi = lambda a, b: a / b


def is_logged_in():
    if session.get('username'):
        return True
    else:
        return False


def create_entry_new_hafta(user_type="loan", **kwargs):
    query_data = dict()
    if user_type == 'debit':
        query_data['id'] = int(kwargs['id'])
        query_data['base_amount'] = float(kwargs['base_amount'])
        try:
            query_data['paid_date'] = datetime.strptime(str(kwargs['startdate']), "%d/%m/%Y")
        except Exception as e:
            query_data['paid_date'] = datetime.strptime(str(kwargs['startdate']), "%Y-%m-%d")
        query_data['remark'] = kwargs['remark']
        crdr_query = CrDrEntry(**query_data)
        db.session.add(crdr_query)
        db.session.commit()
        loan_id = CrDrEntry.query.filter_by(id=crdr_query.id).all()[-1].transaction_id
        total_balance = db_utils.sum_sub_value_in_balance_amount(query_data['base_amount'], 'sub')
        Customer.query.filter_by(id=int(kwargs['id'])).update({'customer_type_crdr': 1})
        db.session.commit()
        tx_hist_query = TransactionHistory(party_id=query_data['id'], loan_id=loan_id, account_type='debit',
                                           amount=query_data['base_amount'],
                                           status='dr', total_balance=total_balance)
        db.session.add(tx_hist_query)
        db.session.commit()

        resp = {'code': 200, 'status': 'entry for debit account created'}
    else:
        query_data['id'] = int(kwargs['id'])
        query_data['base_amount'] = float(kwargs['base_amount'])
        query_data['interest'] = float(kwargs['interest']) if 'interest' in kwargs.keys() else 0
        query_data['total_amount'] = query_data['base_amount'] + query_data['interest']
        query_data['no_installment'] = int(kwargs['noi']) if 'noi' in kwargs.keys() else 0
        try:
            query_data['start_date'] = datetime.strptime(str(kwargs['startdate']), "%d/%m/%Y")
        except Exception as e:
            query_data['start_date'] = datetime.strptime(str(kwargs['startdate']), "%Y-%m-%d")

        query_data['installment_period'] = kwargs['period'] if 'period' in kwargs.keys() else 'monthly'
        query_data['loan_type'] = kwargs['loan_type'] if 'loan_type' in kwargs.keys() else 'flat'
        query_data['last_installment_date'] = query_data['start_date'] + relativedelta(
            months=query_data['no_installment'])
        if query_data['loan_type'] == 'flat':
            total_interest = query_data['interest'] * query_data['no_installment']

        else:
            total_interest = query_data['interest']
        current_pending_interest = General.query.filter_by(
            username=session.get('username')).first().total_interest_pending
        next_pending_interest = current_pending_interest + total_interest
        General.query.filter_by(username=session.get('username')).update(
            {'total_interest_pending': next_pending_interest})
        db.session.commit()
        if user_type == "loan":
            query_data['guarantor_1_name'] = kwargs['guarantor_1_name']
            query_data['guarantor_1_phone'] = int(kwargs['guarantor_1_phone'])
            query_data['guarantor_1_address'] = kwargs['guarantor_1_address']

            if kwargs['guarantor_2_name'] != '':
                query_data['guarantor_2_name'] = kwargs['guarantor_2_name']
                query_data['guarantor_2_phone'] = int(kwargs['guarantor_2_phone'])
                query_data['guarantor_2_address'] = kwargs['guarantor_2_address']
        resp = db_utils.add_new_hafta_entry(user_type=user_type, **query_data)
        if resp['code'] == 200:
            query_data['transaction_id'] = resp['transaction_id']
            # user-table will be created in above method

            resp = add_user_track_data(user_type=user_type, **query_data)
            if user_type == 'loan':
                query_data['emi_amount'] = resp['emi_amount']
                if resp['code'] == 200 and query_data['loan_type'] == 'flat':
                    query_data['paid_amount'] = float(kwargs['paid_amount']) if kwargs['paid_amount'] != '' else 1000
                    resp = db_utils.add_installment(user_type=user_type, **query_data)
                if user_type == "loan":
                    total_balance = db_utils.sum_sub_value_in_balance_amount(query_data['base_amount'], 'sub')
                    tx_hist_query = TransactionHistory(party_id=query_data['id'], loan_id=query_data['transaction_id'],
                                                       account_type='loan',
                                                       amount=query_data['base_amount'],
                                                       status='dr', total_balance=total_balance)
                    db.session.add(tx_hist_query)
                    db.session.commit()
            if user_type == 'account':
                total_balance = db_utils.sum_sub_value_in_balance_amount(query_data['base_amount'], 'sum')
                tx_hist_query = TransactionHistory(party_id=query_data['id'], loan_id=query_data['transaction_id'],
                                                   account_type='account',
                                                   amount=query_data['base_amount'],
                                                   status='cr', total_balance=total_balance)
                db.session.add(tx_hist_query)
                db.session.commit()
    return resp


def add_user_track_data(user_type="loan", **kwargs):
    if kwargs['loan_type'] != 'flat':
        emi_amount = calculate_emi(kwargs['total_amount'], kwargs['no_installment'])
    else:
        emi_amount = kwargs['interest']
    try:
        if user_type == 'account':
            db_utils.add_hafta_track_entry(**{'user_id': kwargs['id'], 'tx_id': kwargs['transaction_id'],
                                              'amount': kwargs['base_amount'], 'date': kwargs['start_date'],
                                              'tx_type': 'cr'})
        else:
            for installment in range(1, kwargs['no_installment'] + 1):
                db_utils.add_hafta_track_entry(
                    **{'user_id': kwargs['id'], 'loan_id': kwargs['transaction_id'], 'emi_amount': emi_amount,
                       'date_to_pay': kwargs['start_date'] + relativedelta(
                           months=installment - 1 if kwargs['loan_type'] == 'flat' else installment),
                       'no_of_installment': installment, "tx_status": 0})
            if kwargs['loan_type'] == 'flat':
                db_utils.add_hafta_track_entry(
                    **{'user_id': kwargs['id'], 'loan_id': kwargs['transaction_id'],
                       'emi_amount': kwargs['base_amount'],
                       'date_to_pay': kwargs['start_date'] + relativedelta(
                           months=installment), 'tx_status': 0,
                       'no_of_installment': installment + 1})
        return {"code": 200, "status": "pending", "emi_amount": emi_amount}
    except Exception as e:
        print(e)
        return {"code": 500, "status": "error while adding track data"}


def get_loan_entries_by_user_id(user_id, user_type="loan"):
    data = db_utils.get_user_loan_entries_by_user_id(user_id, user_type=user_type)
    for val in data:
        val['today'] = datetime.now().date()
        # val['paid_date'] = val['paid_date'].date() if val['paid_date'] is not None else None
        user_data = db_utils.get_user_info_by_id(val['id'])
        val['no_of_pending_installments'] = len(get_pending_installment_of_loan_id(user_id, val['transaction_id']))

        val['loan_type'] = db_utils.get_loan_type_by_loan_id(val['id'], val['transaction_id'], user_type=user_type)
        if val['loan_type'] == "flat":
            val['pending_total_amount'] = val['base_amount']
        else:
            val['pending_total_amount'] = (val['base_amount'] / val['no_installment']) * val[
                'no_of_pending_installments']
        val['user_alias'] = user_data[0].user_alias
        val['user_name'] = user_data[0].user_name
        val['user_phone'] = user_data[0].user_phone
        val['user_address'] = user_data[0].user_address
        val['user_city'] = user_data[0].user_city
    if len(data) == 0:
        user_data = db_utils.get_user_info_by_id(user_id)
        val = {'user_alias': user_data[0].user_alias, 'user_name': user_data[0].user_name,
               'user_phone': user_data[0].user_phone, 'user_address': user_data[0].user_address,
               'user_city': user_data[0].user_city}
        data.append(val)
    return data


def get_account_user_details(user_id):
    data = db_utils.get_user_data(user_id, user_type='account')
    return data


def get_user_details(user_id, user_type='loan', account_type='hafta', loan_status='active'):
    if account_type == 'debit':
        data = CrDrEntry.query.filter_by(id=user_id).order_by(CrDrEntry.paid_date.desc()).all()
        for i, d in enumerate(data):
            user_data = Customer.query.filter_by(id=user_id).first()
            d = convert_table_to_dict_data(d)
            d['user_alias'] = user_data.user_alias
            d['user_name'] = user_data.user_name
            d['user_phone'] = user_data.user_phone
            d['user_address'] = user_data.user_address
            d['user_city'] = user_data.user_city

            data[i] = d
        return data
    else:
        data = db_utils.get_user_data(user_id, user_type=user_type, loan_status=loan_status)
        for val in data:
            val['today'] = datetime.now().date()
            user_data = db_utils.get_user_info_by_id(user_id)

            try:
                # user_data = db_utils.get_user_info_by_id(val['user_id'])
                val['loan_type'] = db_utils.get_loan_type_by_loan_id(val['user_id'], val['loan_id'],
                                                                     user_type=user_type)
                val['date_to_pay'] = val['date_to_pay']
                val['paid_date'] = val['paid_date'].date() if val['paid_date'] is not None else None
            except Exception as e:
                val['date_to_pay'] = None
                pass
            val['user_alias'] = user_data[0].user_alias
            val['user_name'] = user_data[0].user_name
            val['user_phone'] = user_data[0].user_phone
            val['user_address'] = user_data[0].user_address
            val['user_city'] = user_data[0].user_city

        if len(data) == 0:
            val = dict()
            val['today'] = datetime.now().date()
            val['paid_date'] = None
            user_data = db_utils.get_user_info_by_id(user_id)
            val['loan_type'] = None
            val['user_id'] = user_id
            val['user_alias'] = user_data[0].user_alias
            val['user_name'] = user_data[0].user_name
            val['user_phone'] = user_data[0].user_phone
            val['user_address'] = user_data[0].user_address
            val['user_city'] = user_data[0].user_city
            val['loan_id'] = None
            data.append(val)
        return data


def get_report_of_pending_installments_by_date(date, user_type='loan'):
    if user_type == 'loan':
        table_name = HaftEntry
    else:
        table_name = AccountEntry
    columns = ['Name', 'Date', 'Amount',
               'Phone', 'Gua Name', 'Gua Phone']
    df = pd.DataFrame(columns=columns)
    active_users = table_name.query.filter_by(loan_status=0).all()
    checked_users = []
    user_data_dict = dict()
    for user_data in active_users:
        user_data = convert_table_to_dict_data(user_data)
        if user_data['id'] not in checked_users:
            checked_users.append(user_data['id'])
            user_data_pending_installments, _ = get_pending_installments_of_user(user_data['id'], date)
            print('after convert to date')
            if user_data_pending_installments:
                user_data_dict[user_data['id']] = {}
                user_data_dict[user_data['id']]['loans'] = user_data_pending_installments
                user_info = convert_table_to_dict_data(Customer.query.filter_by(id=user_data['id']).first())
                for loan_id, loan_pending_installment_details in user_data_pending_installments.items():
                    if user_data['guarantor_2_name'] is not None:
                        row = pd.Series([user_info['user_name'],
                                         str(loan_pending_installment_details[2]) +"<br/>"+str(loan_id),
                                         str(loan_pending_installment_details[0])+"<br/>"+str(loan_pending_installment_details[3]), user_info['user_phone'],
                                         user_data['guarantor_1_name']+"<br/>"+user_data['guarantor_2_name'], str(user_data['guarantor_1_phone'])+"<br/>"+str(user_data['guarantor_2_phone'])], columns)
                    else:
                        row = pd.Series([user_info['user_name'],
                                         str(loan_pending_installment_details[2]) +"<br/>"+str(loan_id),
                                         str(loan_pending_installment_details[0])+"<br/>"+str(loan_pending_installment_details[3]), user_info['user_phone'],
                                         user_data['guarantor_1_name'],
                                         user_data['guarantor_1_phone']], columns)
                    df = df.append(row, ignore_index=True)
    df = pd.concat([df]*5, ignore_index=True)
    return df


def get_user_entries_between_date(user_id, from_date, to_date, user_type='loan'):
    columns = ['User ID', 'Loan ID', 'No of Installment', 'EMI Date', 'Paid Date', 'Paid Amount']
    df = pd.DataFrame(columns=columns)
    user_entries_proxy = db_utils.get_user_entries_between_date(user_id, from_date, to_date)
    for val in user_entries_proxy:
        row = pd.Series([user_id, val['loan_id'], val['no_of_installment'], val['date_to_pay'].strftime("%d/%m/%Y"),
                         val['paid_date'].date().strftime("%d/%m/%Y"), "{:.2f}".format(val['paid_amount'])], columns)

        df = df.append(row, ignore_index=True)
    pd.set_option('display.max_columns', None)
    return df


def get_user_data_by_loan_id(loan_id):
    try:
        data = []
        user_id = db_utils.get_user_id_from_loan_id(loan_id)
    except Exception as e:
        val = dict()
        val['today'] = datetime.now().date()
        val['paid_date'] = "Not Found"
        user_data = "Not Found"
        val['loan_type'] = "Not Found"
        val['user_id'] = "Not Found"
        val['user_alias'] = "Not Found"
        val['user_name'] = "Not Found"
        val['user_phone'] = "Not Found"
        val['user_address'] = "Not Found"
        val['user_city'] = "Not Found"
        val['loan_id'] = "Not Found"
        data.append(val)
        return data
    data = db_utils.get_user_data_by_loan_id(loan_id)
    for val in data:
        val['today'] = datetime.now().date()
        val['paid_date'] = val['paid_date'].date() if val['paid_date'] is not None else None
        user_data = db_utils.get_user_info_by_id(val['user_id'])
        val['loan_type'] = db_utils.get_loan_type_by_loan_id(val['user_id'], val['loan_id'])
        val['user_alias'] = user_data[0].user_alias
        val['user_name'] = user_data[0].user_name
        val['user_phone'] = user_data[0].user_phone
        val['user_address'] = user_data[0].user_address
        val['user_city'] = user_data[0].user_city
        val['date_to_pay'] = val['date_to_pay'].date()

    if len(data) == 0:
        val = dict()
        val['today'] = datetime.now().date()
        val['paid_date'] = None
        user_data = db_utils.get_user_info_by_id(user_id)
        val['loan_type'] = None
        val['user_id'] = user_id
        val['user_alias'] = user_data[0].user_alias
        val['user_name'] = user_data[0].user_name
        val['user_phone'] = user_data[0].user_phone
        val['user_address'] = user_data[0].user_address
        val['user_city'] = user_data[0].user_city
        val['loan_id'] = None
        data.append(val)

    return data
