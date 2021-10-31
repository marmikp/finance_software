import datetime
import math
from hashlib import md5
from time import sleep

import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import session
from sqlalchemy import or_, and_
from database.model import *

META_DATA = None


def create_html_table(x, length=0, show_col_name=False, lines=1):
    row_data = ''
    dtype_list = []
    for col in x.columns.values.tolist():
        if pd.to_numeric(x[col], errors='coerce').notnull().all() or 'amount' in col:
            dtype_list.append('numeric')
        else:
            dtype_list.append('text')
    if show_col_name:
        row_data += '<tr height:50px;>'
        for col in x.columns.values.tolist():
            row_data += f'<th>{col}</th>'
        row_data += '</tr>'
    row_data += '<tr height:50px;>'
    for i in range(x.shape[0]):
        if length != 0:
            if i == x.shape[0] - 1:
                continue
        if i != 0:
            if (i == 20 and lines == 2) or (i % 21 == 0 and lines == 2 and i != 21) or (i == 30 and lines == 1) or (
                    i % 35 == 0 and lines == 1 and i != 35):
                if i % 21*3 == 0:
                    row_data += "</table>\n<br/><br/><br/></br><table><tr height:50px;>"
                else:
                    row_data += "</table>\n<br/><br/><br/><table><tr height:50px;>"

            else:
                row_data += '\n<tr height:50px;> '
        for j in range(x.shape[1]):
            if pd.isnull(x.iloc[i, j]):
                val = ''
            else:
                val = x.iloc[i, j]
            if dtype_list[j] == 'text':  # The first column

                row_data += '\n <td class = "text_column">' + str(val) + '</td>'

            else:  # second column
                row_data += '\n <td class = "number_column" style="text-align:right;">' + str(val) + '</td>'

        row_data += '\n </tr>'
    if length != 0:
        for i in range(length - x.shape[0]):
            row_data += '\n<tr height:50px;> <td></td><td></td><td></td>\n</tr>'
        row_data += '\n<tr> '
        row_data += '\n <td class = "number_column" style="text-align:right">' + str(
            x.iloc[x.shape[0] - 1, 0]) + '</td>'

        row_data += '\n <td class = "number_column" style="text-align:right">' + str(
            x.iloc[x.shape[0] - 1, 1]) + '</td>'
        row_data += '\n <td class = "number_column" style="text-align:right">' + str(
            x.iloc[x.shape[0] - 1, 2]) + '</td>'
        row_data += '\n </tr>'
    return row_data


def get_user_basic_info_by_loan_id(loan_id):
    user_id = get_user_id_from_loan_id(loan_id)
    customer_data = Customer.query.filter_by(id=user_id).first()
    loan_data = HaftEntry.query.filter_by(transaction_id=loan_id).first()
    data={'user_id': user_id, 'name': customer_data.user_name, 'alias': customer_data.user_alias,
          'address': customer_data.user_address, 'phone': customer_data.user_phone,
          'phone_2': customer_data.user_phone_2,
          'city': customer_data.user_city, 'guarantor_1_name': loan_data.guarantor_1_name,
          'guarantor_2_name': loan_data.guarantor_2_name, 'guarantor_1_phone': loan_data.guarantor_1_phone,
          'guarantor_2_phone': loan_data.guarantor_2_phone, 'guarantor_1_address': loan_data.guarantor_1_address,
          'guarantor_2_address': loan_data.guarantor_2_address}
    return data


def create_general_html_table(x, length=0, show_col_name=False):
    row_data = ''
    dtype_list = []
    for col in x.columns.values.tolist():
        if pd.to_numeric(x[col], errors='coerce').notnull().all() or 'amount' in col:
            dtype_list.append('numeric')
        else:
            dtype_list.append('text')
    if show_col_name:
        row_data += '<tr>'
        for col in x.columns.values.tolist():
            row_data += f'<th>{col}</th>'
        row_data += '</tr>'
    row_data += '<tr>'
    for i in range(x.shape[0]):
        if length != 0:
            if i == x.shape[0] - 1:
                continue
        if i != 0:
            row_data += '\n<tr> '
        for j in range(x.shape[1]):
            if pd.isnull(x.iloc[i, j]):
                val = ''
            else:
                val = x.iloc[i, j]
            if dtype_list[j] == 'text':  # The first column
                if x.columns.values.tolist()[j] == 'id':
                    row_data += '\n <td class = "text_column col-md-2">' + str(val) + '</td>'
                else:
                    row_data += '\n <td class = "text_column col-md-8">' + str(val) + '</td>'

            else:  # second column
                row_data += '\n <td class = "number_column col-md-2" style="text-align:right;">' + str(val) + '</td>'

        row_data += '\n </tr>'
    if length != 0:
        for i in range(length - x.shape[0]):
            row_data += '\n<tr> <td></td><td></td><td></td>\n</tr>'
        row_data += '\n<tr> '
        row_data += '\n <td class = "number_column" style="text-align:right">' + str(
            x.iloc[x.shape[0] - 1, 0]) + '</td>'

        row_data += '\n <td class = "number_column" style="text-align:right">' + str(
            x.iloc[x.shape[0] - 1, 1]) + '</td>'
        row_data += '\n <td class = "number_column" style="text-align:right">' + str(
            x.iloc[x.shape[0] - 1, 2]) + '</td>'
        row_data += '\n </tr>'
    return row_data


def convert_table_to_dict_data(data):
    print("in convert table to dict")
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
    password = md5(password.encode()).hexdigest()
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
            return 1
        else:
            return max_id + 1
    else:
        data = Customer.query.filter_by(id=id).first()
        return data


def get_max_loan_id():
    max_query_id = db.session.query(db.func.max(HaftEntry.transaction_id))
    max_id = db.session.execute(max_query_id).first()[0]
    return max_id + 1


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
    no_installments += 1
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
        for i in range(0, no_of_hafta):
            add_hafta_track_entry(
                **{'user_id': customer_id, 'loan_id': loan_id, 'emi_amount': amount,
                   'date_to_pay': user_data_list[0]['date_to_pay'] + relativedelta(
                       months=i),
                   'no_of_installment': no_installments + i, 'tx_status': 0})

        entry_table.query.filter_by(id=customer_id, transaction_id=loan_id).update(
            {"last_installment_date": entry_table.query.filter_by(id=customer_id,
                                                                  transaction_id=loan_id).first().last_installment_date + relativedelta(
                months=no_of_hafta),
             "no_installment": no_installments + no_of_hafta-1})

        # db.session.commit()
        db.session.commit()
        total_balance = General.query.filter_by(username=session.get('username')).first().total_balance
        tx_hist_query = TransactionHistory(party_id=customer_id, loan_id=loan_id,
                                           account_type='Extend Hafta',
                                           amount=no_of_hafta * amount,
                                           status='', total_balance=total_balance)
        db.session.add(tx_hist_query)
        db.session.commit()
        current_pending_interest = General.query.filter_by(
            username=session.get('username')).first().total_interest_pending
        next_pending_interest = current_pending_interest + (amount * no_of_hafta)
        General.query.filter_by(username=session.get('username')).update(
            {'total_interest_pending': next_pending_interest})
        db.session.commit()
        return {"code": 200, "status": "hafta extend done"}
    except Exception as e:
        print(e)
        return {"code": 500, "status": "error occurred in hafta extension"}


def get_max_transaction_id():
    ll = HaftEntry.query.order_by('transaction_id').all()
    if len(ll) > 0:
        tx_id1 = ll[-1].transaction_id
    else:
        tx_id1 = 0
    ll = AccountEntry.query.order_by('transaction_id').all()
    if len(ll) > 0:
        tx_id2 = ll[-1].transaction_id
    else:
        tx_id2 = 0
    return max(tx_id1, tx_id2)


def get_max_transaction_id_m(user_type):
    if user_type == 'loan':
        ll = HaftEntry.query.order_by('transaction_id').all()
        if len(ll) > 0:
            tx_id1 = ll[-1].transaction_id
        else:
            tx_id1 = 0
    else:
        ll = AccountEntry.query.order_by('transaction_id').all()
        if len(ll) > 0:
            tx_id1 = ll[-1].transaction_id
        else:
            tx_id1 = 0
    return tx_id1


def add_new_hafta_entry(user_type="loan", **kwargs):
    if user_type == "loan":
        kwargs['transaction_id'] = get_max_transaction_id_m(user_type) + 1
        add_query = HaftEntry(**kwargs)
    else:
        kwargs['transaction_id'] = get_max_transaction_id_m(user_type) + 1
        add_query = AccountEntry(**kwargs)

    try:
        db.session.add(add_query)
        db.session.commit()

        sleep(1)
        if user_type == "loan":
            Customer.query.filter_by(id=add_query.id).update({"customer_type_loan": 1})
            create_user_table(kwargs['id'])
        else:
            Customer.query.filter_by(id=add_query.id).update({"customer_type_account": 1})
            create_account_user_table(kwargs['id'])

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


def add_installment(installment_num=1, paid_date=datetime.now(), user_type="loan", **kwargs):
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

            print(user_data_list[0]['tx_hist_id'])
            try:
                TransactionHistory.query.filter(
                    TransactionHistory.tx_id == user_data_list_current[0]['tx_hist_id']).delete()
                # User.query.filter(User.id == 123).delete()
                db.session.commit()
            except Exception as e:
                pass

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
            # stmt = TransactionHistory.delete().where(TransactionHistory.c.tx_id == user_data_list[0]['tx_hist_id'])
            # stmt.execute()

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
                     'total_interest_earned': current_earned_interest + min(kwargs['paid_amount'],
                                                                            each_month_interest)})

            db.session.commit()
            total_balance = General.query.filter_by(username=session.get('username')).first().total_balance
            tx_hist_query = TransactionHistory(party_id=kwargs['id'], loan_id=kwargs['transaction_id'],
                                               account_type='loan emi',
                                               amount=kwargs['paid_amount'],
                                               status='cr', total_balance=total_balance)
            db.session.add(tx_hist_query)
            db.session.commit()
            tx_id = TransactionHistory.query.order_by(TransactionHistory.tx_id.desc()).first().tx_id
            db.engine.execute(
                table.update().where(
                    (table.c.loan_id == kwargs['transaction_id']) & (
                            table.c.no_of_installment == installment_num)).values(
                    {'tx_hist_id': tx_id}))
            db.session.commit()

        return {"code": 200, "status": "installment updated successfully"}
    except Exception as e:
        print(e)
        return {"code": 500, "status": "error in installment update"}


def get_user_data(id=None, loan_type="hafta", user_type='loan', loan_status='active'):
    if id is not None:
        try:
            user_table = META_DATA.tables[str(id)]
            if user_type == 'loan':
                entry_table = HaftEntry
            else:
                entry_table = AccountEntry
            if loan_type == "hafta":
                user_data = []
                if loan_status == 'both':
                    user_active_loans = [val.transaction_id for val in
                                         entry_table.query.filter_by(id=id).all()]
                elif loan_status == 'active':
                    user_active_loans = [val.transaction_id for val in
                                         entry_table.query.filter_by(id=id, loan_status=0).all()]
                else:
                    user_active_loans = [val.transaction_id for val in
                                         entry_table.query.filter_by(id=id, loan_status=1).all()]
                for loan in user_active_loans:

                    if user_type == 'account':
                        user_d = db.engine.execute(
                            user_table.select())
                        user_d_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_d]
                        pending_amount = 0
                        for val in user_d_list:
                            if val['tx_type'] == 'cr':
                                pending_amount += val['amount']
                            else:
                                pending_amount -= val['amount']
                            entry_data = entry_table.query.filter_by(id=id, transaction_id=loan).first()
                            # val['remark'] = entry_data.remark
                            val['base_amount'] = entry_data.base_amount
                        user_d_list[0]['pending_amount'] = pending_amount
                    else:
                        user_d = db.engine.execute(
                            user_table.select().where(user_table.c.loan_id == loan).order_by(
                                user_table.c.tx_status.desc()))
                        user_d_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_d]
                        if user_type == 'debit':
                            for val in user_d_list:
                                entry_data = entry_table.query.filter_by(id=id, transaction_id=loan).first()
                                val['remark'] = entry_data.remark
                                val['base_amount'] = entry_data.base_amount
                        elif user_type == 'loan':
                            for val in user_d_list:
                                entry_data = entry_table.query.filter_by(id=id, transaction_id=loan).first()
                                val['base_amount'] = entry_data.base_amount
                    user_data += user_d_list
                # try:
                #     # user_data = sorted(user_data, key=itemgetter('tx_status'))
                # except Exception as e:
                #     print(e)

                print(user_data)
                return user_data
        except Exception as e:
            return [{}]
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
            for data in user_d_list:
                if type(data['date_to_pay']) == str:
                    try:
                        data['date_to_pay'] = datetime.strptime(data['date_to_pay'], "%Y-%m-%d %H:%M:%S.%f")
                    except:
                        pass
                if data['paid_date'] is not None and type(data['paid_date']) == str:
                    try:
                        data['paid_date'] = datetime.strptime(data['paid_date'], "%Y-%m-%d %H:%M:%S.%f")
                    except:
                        pass
            user_data += user_d_list
            # user_data = sorted(user_data, key=itemgetter('tx_status'))
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


def get_users_details(loan_status="active", user_type="loan", all_entries=False):
    if user_type == 'loan':
        if all_entries:
            customer_data = Customer.query.all()
        else:
            customer_data = Customer.query.filter_by(customer_type_account=0, customer_type_crdr=0).all()
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
                data_fetch = AccountEntry.query.filter_by(id=data['id'], loan_status=0).all()
                data['num_loan_account'] = len(data_fetch)
                data['loan_id'] = data_fetch[0].transaction_id
            data['customer_type'] = "account"
            pass
        if data['customer_type_loan']:
            if all_entries or loan_status == 'both':
                loan_data = HaftEntry.query.filter_by(id=data['id']).all()
                data['num_loan_hafta'] = len(HaftEntry.query.filter_by(id=data['id'], loan_status=0).all())
            else:
                loan_data = HaftEntry.query.filter_by(id=data['id'], loan_status=0).all()
                data['num_loan_hafta'] = len(loan_data)
            data['loans'] = ''
            for loan in loan_data:
                data['loans'] += str(loan.transaction_id) + ", "
            data['loans'] = data['loans'][:-2]
            data_fetch = HaftEntry.query.filter_by(id=data['id']).all()
            data['loan_id'] = data_fetch[0].transaction_id
            data['customer_type'] = "loan"
        if data['customer_type_account'] and data['customer_type_loan']:
            data['customer_type'] = "both"
        customer_data[i] = data
        print("customer data: ", customer_data)
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
    pending_amount = 0
    if get_loan_type_by_loan_id(loan_id=loan_id) == "flat":
        for val in user_data_list:
            pending_amount += val['emi_amount']
        pending_amount -= entry_table.query.filter_by(id=user_id, transaction_id=loan_id).first().base_amount
    else:
        loan_entry = entry_table.query.filter_by(id=user_id, transaction_id=loan_id).first()
        one_month_interest = loan_entry.interest / loan_entry.no_installment
        pending_amount = one_month_interest * len(user_data_list)
    total_pending_interst = General.query.filter_by(username=session.get('username')).first().total_interest_pending
    General.query.filter_by(username=session.get('username')).update({'total_interest_pending': total_pending_interst -
                                                                                                pending_amount})
    db.session.commit()
    latest_installment_no = user_data_list[0]['no_of_installment']
    db.engine.execute(
        table.update().where(
            (table.c.loan_id == loan_id) & (
                    table.c.no_of_installment == latest_installment_no)).values(
            {'paid_amount': amount, 'paid_date': datetime.now().date(), 'tx_status': 1}))
    db.session.commit()

    for i, d in enumerate(user_data_list):
        if i == 0:
            continue
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

    query = TransactionHistory(party_id=user_id, loan_id=loan_id, account_type='close loan',
                               amount=amount, status='cr',
                               total_balance=get_amount_value_from_general(session.get('username')),
                               tx_date=datetime.now().date())
    db.session.add(query)
    db.session.commit()

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
        if type(val['date_to_pay']) == str:
            loan_id_dict[val['loan_id']][2] = datetime.strptime(val['date_to_pay'].split(" ")[0], "%Y-%m-%d").date().strftime("%d/%m/%Y")

        else:
            loan_id_dict[val['loan_id']][2] = val['date_to_pay'].date().strftime("%d/%m/%Y")
        val['date_to_pay'] = loan_id_dict[val['loan_id']][2]
        loan_id_dict[val['loan_id']][3] = len(emis_dict_count)
    return loan_id_dict, emis_dict


def get_account_user_entries(user_id, from_date=datetime.now().date() - relativedelta(months=1),
                             date=datetime.now().date()):
    entry_table = META_DATA.tables[str(user_id)]
    user_entries = db.engine.execute(entry_table.select().where(
        (entry_table.c.date <= date) & (entry_table.c.date >= from_date)))
    user_entries = [{column: value for column, value in rowproxy.items()} for rowproxy in user_entries]
    # get opening balance
    user_entries_opening = db.engine.execute(entry_table.select().where((entry_table.c.date < from_date)))
    user_entries_opening = [{column: value for column, value in rowproxy.items()} for rowproxy in user_entries_opening]
    if len(user_entries_opening) > 0:
        credit_amt = 0
        debit_amt = 0
        for entry in user_entries_opening:
            if entry['tx_type'] == 'cr':
                credit_amt += entry['amount']
            else:
                debit_amt += entry['amount']
        if debit_amt == credit_amt:
            opening_balance_row = pd.Series([-1, 0, 0, from_date.strftime("%d/%m/%Y"), '', 'Opening Balance'],
                                            ['tx_id', 'credit', 'debit', 'date', 'tx_type', 'remark'])
        elif debit_amt > credit_amt:
            opening_balance_row = pd.Series(
                [-1, '', debit_amt - credit_amt, from_date.strftime("%d/%m/%Y"), '', 'Opening Balance'],
                ['tx_id', 'credit', 'debit', 'date', 'tx_type', 'remark'])
        else:
            opening_balance_row = pd.Series(
                [-1, credit_amt - debit_amt, '', from_date.strftime("%d/%m/%Y"), '', 'Opening Balance'],
                ['tx_id', 'credit', 'debit', 'date', 'tx_type', 'remark'])
    else:
        opening_balance_row = pd.Series([-1, 0, 0, from_date.strftime("%d/%m/%Y"), '', 'Opening Balance'],
                                        ['tx_id', 'credit', 'debit', 'date', 'tx_type', 'remark'])
    for i, val in enumerate(user_entries):
        val['date'] = val['date'].date().strftime("%d/%m/%Y")
        user_entries[i] = val
        if val['tx_type'] == 'cr':
            val['credit'] = val['amount']
            val['debit'] = None
        else:
            val['debit'] = val['amount']
            val['credit'] = None

    df = pd.DataFrame(columns=['tx_id', 'credit', 'debit', 'date', 'tx_type', 'remark'])
    df = df.append(opening_balance_row, ignore_index=True)
    for val in user_entries:
        row = pd.Series([val['tx_id'], val['credit'], val['debit'], val['date'], val['tx_type'],
                         val['remark']], ['tx_id', 'credit', 'debit', 'date', 'tx_type', 'remark'])
        df = df.append(row, ignore_index=True)
    return create_html_table(df, show_col_name=True)


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
    day_transactions_credit = TransactionHistory.query.filter_by(tx_date=date, status='cr').all()
    credit_amount = 0
    day_transactions_debit = TransactionHistory.query.filter_by(tx_date=date, status='dr').all()
    debit_amount = 0
    for i, d in enumerate(day_transactions_credit):
        cust_data = Customer.query.filter_by(id=d.party_id).first()
        name = cust_data.user_name

        day_transactions_credit[i] = convert_table_to_dict_data(d)
        if cust_data.customer_type_account == 1:
            day_transactions_credit[i]['loan_id'] = cust_data.user_alias
        day_transactions_credit[i]['name'] = name
        credit_amount += d.amount
    day_transactions_credit = pd.DataFrame.from_dict(day_transactions_credit)
    # if len(day_transactions_credit) > 0:
    #     day_transactions_credit['loan_id'] = day_transactions_credit['loan_id'].astype(int)

    for i, d in enumerate(day_transactions_debit):
        cust_data = Customer.query.filter_by(id=d.party_id).first()
        name = cust_data.user_name
        day_transactions_debit[i] = convert_table_to_dict_data(d)
        day_transactions_debit[i]['name'] = name
        if cust_data.customer_type_account == 1:
            day_transactions_debit[i]['loan_id'] = cust_data.user_alias
        debit_amount += d.amount
    day_transactions_debit = pd.DataFrame.from_dict(day_transactions_debit)
    day_transactions_debit = day_transactions_debit.append(pd.Series(['Cash', credit_amount - debit_amount], ['name',
                                                                                                              'amount']),
                                                           ignore_index=True)
    if day_transactions_credit.shape[0] > day_transactions_debit.shape[0]:
        for i in range(day_transactions_credit.shape[0] - day_transactions_debit.shape[0] + 2):
            day_transactions_debit = day_transactions_debit.append(pd.Series(), ignore_index=True)
        for i in range(2):
            day_transactions_credit = day_transactions_credit.append(pd.Series(), ignore_index=True)
    else:
        for i in range(day_transactions_debit.shape[0] - day_transactions_credit.shape[0] + 2):
            day_transactions_credit = day_transactions_credit.append(pd.Series(), ignore_index=True)
        for i in range(2):
            day_transactions_debit = day_transactions_debit.append(pd.Series(), ignore_index=True)
    day_transactions_debit = day_transactions_debit.append(
        pd.Series(['Total', day_transactions_debit['amount'].sum()], ['name', 'amount']),
        ignore_index=True)
    day_transactions_credit = day_transactions_credit.append(pd.Series(['Total', credit_amount], ['name', 'amount']),
                                                             ignore_index=True)

    return {'credit_transactions': day_transactions_credit, 'debit_transactions': day_transactions_debit,
            'credit_amount': credit_amount, 'debit_amount': debit_amount}


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


def get_user_due_amount(user_id, account_type='loan'):
    entry_table = META_DATA.tables[str(user_id)]
    pending_entries = db.engine.execute(entry_table.select().where(
        (entry_table.c.user_id == user_id) & (entry_table.c.tx_status == 0) & (entry_table.c.date_to_pay <
                                                                               datetime.now().date())))
    pending_entries = [{column: value for column, value in rowproxy.items()} for rowproxy in pending_entries]
    total_amount = 0
    for val in pending_entries:
        total_amount += val['emi_amount']
    if account_type != 'account':
        total_amount *= -1
    return total_amount


def get_general_report():
    general_data = General.query.filter_by(username=session.get('username')).first()
    all_user_data = pd.DataFrame(columns=['id', 'name', 'amount'])
    columns = ['id', 'name', 'amount']
    hafta_entry_users = HaftEntry.query.filter_by(loan_status=0).all()
    for user_data in hafta_entry_users:
        # all_user_data[str(user_data.transaction_id) + " - " + Customer.query.filter_by(
        #     id=user_data.id).first().user_name] = get_user_pending_amount(
        #     user_data.id) * (-1)
        row = pd.Series([str(user_data.transaction_id), Customer.query.filter_by(
            id=user_data.id).first().user_name, get_user_pending_amount(user_data.id) * (-1)], ['id', 'name', 'amount'])
        all_user_data = all_user_data.append(row, ignore_index=True)

    hafta_entry_users = AccountEntry.query.filter_by(loan_status=0).all()
    account_user_data = pd.DataFrame(columns=['id', 'name', 'amount'])
    for user_data in hafta_entry_users:
        value = get_account_user_pending_amount(user_data.id)
        if value == 0:
            continue
        if value < 0:
            try:
                alias = Customer.query.filter_by(id=user_data.id).first().user_alias
            except Exception as e:
                alias = ''
            # account_user_data[
            #     str(alias) + " - " + Customer.query.filter_by(id=user_data.id).first().user_name] = value * (-1)
            row = pd.Series([alias, Customer.query.filter_by(id=user_data.id).first().user_name, value * (-1)],
                            ['id', 'name', 'amount'])
            account_user_data = account_user_data.append(row, ignore_index=True)
        else:
            try:
                alias = Customer.query.filter_by(id=user_data.id).first().user_alias
            except Exception as e:
                alias = ''
            # all_user_data[
            #     str(alias) + " - " + Customer.query.filter_by(
            #         id=user_data.id).first().user_name] = value
            row = pd.Series([alias, Customer.query.filter_by(id=user_data.id).first().user_name, value],
                            ['id', 'name', 'amount'])
            all_user_data = all_user_data.append(row, ignore_index=True)

    customer_entries = Customer.query.filter_by(customer_type_crdr=1).all()
    for entry in customer_entries:
        customer_data = CrDrEntry.query.filter_by(id=entry.id).all()
        amount = 0
        for data in customer_data:
            amount += data.base_amount
        all_user_data = all_user_data[
            str(entry.id) + " - " + Customer.query.filter_by(id=entry.id).first().user_name] = amount

    # df_dict = {'name': list(all_user_data.keys()), 'value': list(all_user_data.values())}
    # df_dict['name'].append('CASH')
    # df_dict['name'].append('Total')
    # df_dict['value'].append(general_data.total_balance)
    # df_dict['value'].append(np.array(df_dict['value']).sum())

    all_user_data = all_user_data.append(pd.Series(['', 'CASH', general_data.total_balance], columns),
                                         ignore_index=True)
    all_user_data = all_user_data.append(pd.Series(['', 'Grand Total', all_user_data['amount'].sum()], columns),
                                         ignore_index=True)

    # user_data_df = pd.DataFrame.from_dict(df_dict) user_data_df.style.set_properties(**{'text-align': 'right'})
    # general_table_dict = {'name': ['Interest'] + list(account_user_data.keys()), 'value': [math.ceil(
    # general_data.total_interest_earned + general_data.total_interest_pending)] + list( account_user_data.values())}
    account_user_data = account_user_data.append(
        pd.Series(['', 'Interest', math.ceil(general_data.total_interest_earned +
                                             general_data.total_interest_pending)], columns),
        ignore_index=True)
    account_user_data = account_user_data.append(
        pd.Series(['', 'Grand Total', account_user_data['amount'].sum()], columns),
        ignore_index=True)
    # vv = 0
    # for val in general_table_dict['value']:
    #     vv += val
    # general_table_dict['name'].append('Total')
    # general_table_dict['value'].append(vv)
    # general_df = pd.DataFrame.from_dict(general_table_dict)
    # general_df.style.set_properties(**{'text-align': 'right'})
    return {'general': create_general_html_table(account_user_data, all_user_data.shape[0]), 'all_transaction':
        create_general_html_table(all_user_data)}


def get_account_user_pending_amount(user_id):
    if user_id in ['CASH', 'C', 'CA', 'CAS']:
        return get_amount_value_from_general(session.get('username'))
    user_id = int(user_id)
    try:
        user_table = META_DATA.tables[str(user_id)]
        amount_data = db.engine.execute(user_table.select())
        amount_data = [{column: value for column, value in rowproxy.items()} for rowproxy in amount_data]
        pending_amount = 0
        for data in amount_data:
            if data['tx_type'] == 'cr':
                pending_amount -= data['amount']
            else:
                pending_amount += data['amount']
        return pending_amount
    except Exception as e:
        return 0


def add_account_entry(data):
    try:
        user_table = META_DATA.tables[str(data['user_id'])]
        if data['amount_type'] == 'credit':
            tx_id = AccountEntry.query.filter_by(id=int(data['user_id'])).first().transaction_id
            status = 'cr'
            db.engine.execute(user_table.insert(), **{'user_id': data['user_id'], 'tx_id': tx_id, 'amount':
                data['amount_new'], 'date': datetime.strptime(data['date'], '%d/%m/%Y'), 'tx_type': 'cr',
                                                      'remark': data['remark']})
            sum_sub_value_in_balance_amount(float(data['amount_new']), 'sum')
        else:
            if get_amount_value_from_general(session.get('username')) < float(data['amount_new']):
                return {'code': 500, 'status': 'Balance is low to pay'}
            tx_id = AccountEntry.query.filter_by(id=int(data['user_id'])).first().transaction_id
            status = 'dr'
            db.engine.execute(user_table.insert(), **{'user_id': data['user_id'], 'tx_id': tx_id, 'amount':
                data['amount_new'], 'date': datetime.strptime(data['date'], '%d/%m/%Y'), 'tx_type': 'dr',
                                                      'remark': data['remark']})
            sum_sub_value_in_balance_amount(float(data['amount_new']), 'sub')

        query = TransactionHistory(party_id=data['user_id'], loan_id=tx_id, account_type='account',
                                   amount=data['amount_new'], status=status,
                                   total_balance=get_amount_value_from_general(session.get('username')),
                                   tx_date=datetime.now().date())
        db.session.add(query)
        db.session.commit()
        return {'code': 200, 'status': 'entry updated successfully'}
    except Exception as e:
        print(e)
        return {'code': 500, 'status': 'server side error occured add_account_entry'}


def customer_type_by_user_id(user_id):
    cst_details = Customer.query.filter_by(id=user_id).first()
    if user_id == 'CASH':
        return 'self'
    if cst_details.customer_type_loan == 1 and cst_details.customer_type_account == 1:
        return 'both'
    elif cst_details.customer_type_loan == 1:
        return 'loan'
    elif cst_details.customer_type_account == 1:
        return 'account'
    else:
        return 'nothing'


def add_account_entry_by_lenar_denar(lenar_user_user_id, denar_user_user_id, amount, remark, date):
    if customer_type_by_user_id(lenar_user_user_id) in ['account', 'both']:
        transaction_type = 'debit'
    elif customer_type_by_user_id(denar_user_user_id) in ['account', 'both']:
        transaction_type = 'credit'
    else:
        return {"code": 500, 'status': 'Provided account is not account type'}

    if lenar_user_user_id != 'CASH':
        user_id = lenar_user_user_id
    else:
        user_id = denar_user_user_id

    return add_account_entry(
        data={'amount_new': amount, 'user_id': user_id, 'amount_type': transaction_type, 'remark': remark,
              'date': date})


def get_user_entries_report(user_id):
    user_table = META_DATA.tables[str(user_id)]
    columns = ['Loan ID', 'No of Installment', 'EMI Amount', 'EMI Date', 'Paid Date', 'Paid Amount', 'Status']
    user_data = db.engine.execute(user_table.select())
    user_data_list = [{column: value for column, value in rowproxy.items()} for rowproxy in user_data]
    df = pd.DataFrame(columns=columns)
    for val in user_data_list:
        if val['tx_status']:
            date = val['paid_date'].date().strftime("%d/%m/%Y")
            paid_amount = "{:.2f}".format(val['paid_amount'])
        else:
            date = ''
            paid_amount = ''

        row = pd.Series(
            [val['loan_id'], val['no_of_installment'], val['emi_amount'], val['date_to_pay'].strftime("%d/%m/%Y"),
             date, paid_amount, 'Paid' if val['tx_status'] else 'Pending'], columns)

        df = df.append(row, ignore_index=True)
    return df
