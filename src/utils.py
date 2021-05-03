from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import session

from database import db_utils
from database.db_utils import get_pending_installment_of_loan_id, convert_table_to_dict_data, \
    get_pending_installments_of_user
from database.model import db, HaftEntry, CrDrEntry, AccountEntry, Customer


calculate_emi = lambda a, b: a / b


def is_logged_in():
    session['username'] = 'marmik'
    if session.get('username'):
        return True
    else:
        return False


def create_entry_new_hafta(user_type="loan", **kwargs):
    query_data = dict()
    if user_type == 'debit':
        query_data['id'] = int(kwargs['id'])
        query_data['base_amount'] = float(kwargs['base_amount'])
        query_data['paid_date'] = datetime.strptime(str(kwargs['startdate']), "%Y-%m-%d")
        query_data['remark'] = kwargs['remark']
        crdr_query = CrDrEntry(**query_data)
        db.session.add(crdr_query)
        db.session.commit()
        db_utils.sum_sub_value_in_balance_amount(query_data['base_amount'], 'sub')
        Customer.query.filter_by(id=int(kwargs['id'])).update({'customer_type_crdr': 1})
        db.session.commit()
        resp = {'code': 200, 'status': 'entry for debit account created'}
    else:
        query_data['id'] = int(kwargs['id'])
        query_data['base_amount'] = float(kwargs['base_amount'])
        query_data['interest'] = float(kwargs['interest'])
        query_data['total_amount'] = query_data['base_amount'] + query_data['interest']
        query_data['no_installment'] = int(kwargs['noi'])
        query_data['start_date'] = datetime.strptime(str(kwargs['startdate']), "%Y-%m-%d")
        query_data['installment_period'] = kwargs['period']
        query_data['loan_type'] = kwargs['loan_type']
        query_data['last_installment_date'] = query_data['start_date'] + relativedelta(
            months=query_data['no_installment'])
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
            query_data['emi_amount'] = resp['emi_amount']
            if resp['code'] == 200 and query_data['loan_type'] == 'flat':
                query_data['paid_amount'] = float(kwargs['paid_amount']) if kwargs['paid_amount'] != '' else 1000
                resp = db_utils.add_installment(user_type=user_type, **query_data)
            if user_type == "loan":
                db_utils.sum_sub_value_in_balance_amount(query_data['base_amount'], 'sub')
            else:
                db_utils.sum_sub_value_in_balance_amount(query_data['base_amount'], 'sum')
    return resp


def add_user_track_data(user_type="loan", **kwargs):
    if kwargs['loan_type'] != 'flat':
        emi_amount = calculate_emi(kwargs['total_amount'], kwargs['no_installment'])
    else:
        emi_amount = kwargs['interest']
    try:
        for installment in range(0, kwargs['no_installment']):
            db_utils.add_hafta_track_entry(
                **{'user_id': kwargs['id'], 'loan_id': kwargs['transaction_id'], 'emi_amount': emi_amount,
                   'date_to_pay': kwargs['start_date'] + relativedelta(
                       months=installment if kwargs['loan_type'] == 'flat' else installment + 1),
                   'no_of_installment': installment, "tx_status": 0})
        if kwargs['loan_type'] == 'flat':
            db_utils.add_hafta_track_entry(
                **{'user_id': kwargs['id'], 'loan_id': kwargs['transaction_id'], 'emi_amount': kwargs['base_amount'],
                   'date_to_pay': kwargs['start_date'] + relativedelta(
                       months=installment + 1), 'tx_status': 0,
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
    return data


def get_user_details(user_id, user_type='loan', account_type='hafta'):

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
        data = db_utils.get_user_data(user_id, user_type=user_type)
        for val in data:
            val['today'] = datetime.now().date()
            val['paid_date'] = val['paid_date'].date() if val['paid_date'] is not None else None
            user_data = db_utils.get_user_info_by_id(val['user_id'])
            val['loan_type'] = db_utils.get_loan_type_by_loan_id(val['user_id'], val['loan_id'], user_type=user_type)
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
    columns = ['User ID', 'User Alias', 'User Name', 'User Phone', 'User Address', 'Loan ID', 'Pending Emis',
               'Pending Amount']
    df = pd.DataFrame(columns=columns)
    active_users = table_name.query.filter_by(loan_status=0).all()
    checked_users = []
    user_data_dict = dict()
    for user_data in active_users:
        user_data = convert_table_to_dict_data(user_data)
        if user_data['id'] not in checked_users:
            checked_users.append(user_data['id'])
            user_data_pending_installments, _ = get_pending_installments_of_user(user_data['id'], date)
            if user_data_pending_installments:
                user_data_dict[user_data['id']] = {}
                user_data_dict[user_data['id']]['loans'] = user_data_pending_installments
                user_info = convert_table_to_dict_data(Customer.query.filter_by(id=user_data['id']).first())
                for loan_id, loan_pending_installment_details in user_data_pending_installments.items():
                    row = pd.Series([user_info['id'], user_info['user_alias'], user_info['user_name'],
                                     user_info['user_phone'], user_info['user_address'], loan_id,
                                     loan_pending_installment_details[1], loan_pending_installment_details[0]], columns)
                    df = df.append(row, ignore_index=True)

    return df


def get_user_entries_between_date(user_id, from_date, to_date, user_type='loan'):
    columns = ['User ID', 'Loan ID', 'No of Installment', 'EMI Date', 'Paid Date', 'Paid Amount']
    df = pd.DataFrame(columns=columns)
    user_entries_proxy = db_utils.get_user_entries_between_date(user_id, from_date, to_date)
    for val in user_entries_proxy:
        row = pd.Series([user_id, val['loan_id'], val['no_of_installment'], val['date_to_pay'],
                         val['paid_date'].date(), "{:.2f}".format(val['paid_amount'])], columns)

        df = df.append(row, ignore_index=True)
    pd.set_option('display.max_columns', None)
    df_html = df.to_html(classes='mystyle')
    html_string = f'''
    <html>
      <head><title>HTML Pandas Dataframe with CSS</title></head>
      <link rel="stylesheet" type="text/css" href="df_style.css"/>
      <body>
        {df_html}
      </body>
    </html>
    '''
    # HTML(string=html_string).write_pdf('html_view.pdf', stylesheets=["df_style.css"])
    return df

