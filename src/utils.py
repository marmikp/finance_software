from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import session

from database import db_utils
from database.db_utils import get_pending_installment_of_loan_id, META_DATA
from database.model import db, HaftEntry

calculate_emi = lambda a, b: a / b


def is_logged_in():
    if session.get('username'):
        return True
    else:
        return False


def create_entry_new_hafta(user_type="loan", **kwargs):
    query_data = dict()
    query_data['id'] = int(kwargs['id'])
    query_data['base_amount'] = float(kwargs['base_amount'])
    query_data['interest'] = float(kwargs['interest'])
    query_data['total_amount'] = query_data['base_amount'] + query_data['interest']
    query_data['no_installment'] = int(kwargs['noi'])
    query_data['start_date'] = datetime.strptime(str(kwargs['startdate']), "%Y-%m-%d")
    query_data['installment_period'] = kwargs['period']
    query_data['loan_type'] = kwargs['loan_type']
    query_data['last_installment_date'] = query_data['start_date'] + relativedelta(months=query_data['no_installment'])
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
                   'no_of_installment': installment+1})
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
            val['pending_total_amount'] = (val['base_amount'] / val['no_installment']) * val['no_of_pending_installments']
        val['user_alias'] = user_data[0].user_alias
        val['user_name'] = user_data[0].user_name
        val['user_phone'] = user_data[0].user_phone
        val['user_address'] = user_data[0].user_address
        val['user_city'] = user_data[0].user_city
    return data


def get_user_details(user_id, user_type='loan'):
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


