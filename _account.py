import traceback
from functools import partial
from hashlib import md5
from shutil import copy
from subprocess import check_output
from sys import argv
from threading import Thread
from time import strftime

import numpy as np
from os import path#, startfile
import pandas as pd
from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QMessageBox
from dateutil.relativedelta import relativedelta
from flask import Flask, request, render_template, session, redirect
from markupsafe import Markup
from qt_thread_updater import get_updater
from sqlalchemy import MetaData

import config
import src.utils
from datetime import datetime
from database import db_utils, model
from database.db_utils import get_users_details, create_html_table, get_user_pending_amount, get_user_due_amount, \
    get_user_id_from_loan_id
from database.model import db, General, Customer
from src.utils import is_logged_in, create_entry_new_hafta

if path.exists("api-ms-win-core-heat-key-l1-1-0-1.dll"):
    with open("api-ms-win-core-heat-key-l1-1-0-1.dll", "r") as file:
        key = file.readline()
    if True:#md5(check_output('wmic csproduct get uuid').decode().split('\n')[1].strip().encode()).hexdigest() == key:
        app = Flask(__name__, template_folder='web', static_folder='web')
        app.secret_key = '123456'
        app.config['SESSION_TYPE'] = 'filesystem'
        model.init_database(app)
        with app.app_context():
            db_utils.META_DATA = MetaData(bind=db.session.get_bind(), reflect=True)


        @app.route("/api/test", methods=['POST', 'GET'])
        def test():
            try:
                if request.method == "POST":
                    request_data = request.form.to_dict()
                else:
                    request_data = request.args.to_dict()
                url = request_data['url']
                data = {}
                for key, val in request_data.items():
                    if key == 'url':
                        continue
                    data[key] = val
                call = partial(window.show_new_window, url, data)
                call.__name__ = "my_call"

                get_updater().call_in_main(call)
                return "success"
            except Exception as e:
                print(e)
                return "Failure"


        @app.route('/api/hafta/add_collection_by_loan_id', methods=['POST', 'GET'])
        def add_collection_by_loan_id():
            return render_template('add_collection_by_loan_id.html')


        ######## GENERAL ########
        @app.route('/', methods=['GET', 'POST'])
        def index():
            if session.get('username'):
                data = db_utils.get_index_form_data_total()
                data['today'] = datetime.now().strftime("%A, %d %B, %Y")
                data['pending_amount'] = db_utils.get_total_pending_amount()
                data['total_interest'] = float(data['total_interest_earned']) + float(data['total_interest_pending'])
                return render_template('template/demo/vertical-default-dark/pages/dashboard1.html', data=data)
            else:
                return redirect('/api/user/login')


        @app.route('/api/user/signup', methods=['GET'])
        def signup():
            try:
                args = {'username': request.args['username'], 'password': request.args['password']}
                print(args)
                db_utils.signup(**args)
                return "success"
            except Exception as e:
                return str(e)


        @app.route('/api/user/login', methods=['POST', 'GET'])
        def login():
            if session.get('username'):
                return redirect('/')
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                login_check = db_utils.login(username, password)
                if login_check['code'] == 200:
                    session['username'] = username
                    return redirect("/")
                else:
                    return render_template('template/demo/vertical-default-dark/pages/login.html', data="invalid username or password")
            else:

                return render_template('template/demo/vertical-default-dark/pages/login.html')


        @app.route("/api/add_new_customer", methods=['POST', 'GET'])
        def add_new_customer():
            data = request.form.to_dict()
            data_query = dict()
            data_query['id'] = data['id']
            data_query['user_name'] = data['name']
            data_query['user_alias'] = data['alias']
            data_query['user_address'] = data['address']
            data_query['user_phone'] = data['phone']
            data_query['user_city'] = data['city']

            if 'debit' not in data.keys():
                data_query['user_phone_2'] = data['phone_2'] if 'phone_2' in data.keys() else 0
            db_resp = db_utils.add_new_customer(**data_query)
            return db_resp


        ############## HAFTA ##############
        @app.route('/api/hafta', methods=['GET', 'POST'])
        def hafta():
            if session.get('username'):
                data = db_utils.get_users_details(loan_status='both')
                today = datetime.now().strftime("%A, %d %B, %Y")
                print(data)
                return render_template('template/demo/vertical-default-dark/pages/loanLists1.html', data=data, today=today)
            else:
                return redirect('/api/user/login')


        @app.route('/api/hafta/new_hafta_entry_dialog', methods=['POST', 'GET'])
        def new_hafta_entry_dialog(id=None):
            if request.method == "POST":
                request_data = request.form.to_dict()
            else:
                request_data = request.args.to_dict()

            if not session.get('username'):
                # TODO : code to close current dialog and open login screen in mainwindow
                return "logged out"
            max_id = db_utils.get_max_customer_id(id)
            max_loan_id = db_utils.get_max_loan_id()
            data = {'max_id': max_id, 'today': datetime.now().date(), 'max_loan_id': max_loan_id}
            total_balance = General.query.filter_by(username=session.get('username')).first().total_balance
            data['total_amount'] = total_balance
            data['today'] = datetime.now().strftime("%A, %d %B, %Y")
            if 'debit' in request_data.keys():
                return render_template('templates/usermain_debit.html', data=data)
            else:
                return render_template('template/demo/vertical-default-dark/pages/addNewloan.html', data=data)


        @app.route('/api/hafta/current_user_hafta_entry_dialog', methods=['POST', 'GET'])
        def current_user_hafta_entry_dialog(id=None):
            if request.method == "POST":
                data = src.utils.get_user_details(request.form['user_id'])
                data = data[0]
                request_data = request.form.to_dict()
                data['max_id'] = request.form['user_id']
            else:
                data = src.utils.get_user_details(request.args['user_id'])
                data = data[0]
                request_data = request.args.to_dict()
                data['max_id'] = request.args['user_id']
            try:
                total_balance = General.query.filter_by(username=session.get('username')).first().total_balance
                data['total_amount'] = total_balance
                resp = render_template('templates/usermain.html', data=data)
            except Exception as e:
                print(e)
            return resp



        @app.route('/api/hafta/current_user_hafta_entry', methods=['POST', 'GET'])
        def current_user_hafta_entry():
            return new_hafta_entry(current_user=True)


        @app.route('/api/hafta/new_hafta_entry', methods=['POST', 'GET'])
        def new_hafta_entry(current_user=False):
            if not is_logged_in():
                # TODO : code to close current dialog and open login screen in mainwindow
                return "logged out"
            if request.method == "POST":
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()
            if not current_user:
                if 'debit' in data.keys():
                    resp = add_new_customer()
                else:
                    resp = add_new_customer()
            entry_added_flag = False
            try:
                if data['base_amount'].isnumeric():
                    if resp['code'] == 200:
                        if 'debit' in list(data.keys()):
                            resp = create_entry_new_hafta(**data, user_type='debit')
                        else:
                            resp = create_entry_new_hafta(**data)
                        if resp['code'] == 200:
                            entry_added_flag = True
            except Exception as e:
                print(e)

            if entry_added_flag:
                return {'code': 200, 'status': 'user added with hafta'}

            return resp


        @app.route('/api/hafta/extend_hafta_dialog', methods=['POST', 'GET'])
        def extend_hafta_dialog():
            if request.method == "POST":
                user_id = request.form['user_id']
                data = src.utils.get_user_details(user_id, loan_status='both')

            else:
                user_id = request.args['user_id']
                data = src.utils.get_user_details(user_id, loan_status='both')
            loan_id_list = []
            for d in data:
                try:
                    if d['loan_id'] in loan_id_list:
                        continue
                    else:
                        loan_id_list.append(d['loan_id'])
                except Exception as e:
                    pass

            total_pending_amount = db_utils.get_user_pending_amount(int(user_id))
            ll, _ = db_utils.get_pending_installments_of_user(int(user_id), datetime.now().date())
            total_due_amount = 0
            for i, val in ll.items():
                total_due_amount += val[0]
            data_rander = {'data': data, 'user_id': int(user_id), 'loan_id_list': loan_id_list,
                           'date_today': datetime.now().date(), 'total_pending_amount': total_pending_amount,
                           'total_due_amount': total_due_amount}
            return render_template('template/demo/vertical-default-dark/pages/partyInfo.html', data=data_rander)


        @app.route('/api/hafta/customer_edit_dialog', methods=['POST', 'GET'])
        def customer_edit_dialog():
            if request.method == "POST":
                data = db_utils.get_user_info_by_id(request.form['user_id'], return_type="dict")
            else:
                data = db_utils.get_user_info_by_id(request.args['user_id'], return_type="dict")

            print(data)

            return render_template('template/demo/vertical-default-dark/pages/editCustomerLoan.html', data=data[0])


        @app.route('/api/hafta/customer_edit_account_dialog', methods=['POST', 'GET'])
        def customer_edit_account_dialog():
            if request.method == "POST":
                data = db_utils.get_user_info_by_id(request.form['user_id'], return_type="dict", user_type='account')
            else:
                data = db_utils.get_user_info_by_id(request.args['user_id'], return_type="dict", user_type='account')

            print(data)

            return render_template('template/demo/vertical-default-dark/pages/editCustomerAccount.html', data=data[0])


        @app.route('/api/hafta/customeredit', methods=['POST', 'GET'])
        def extend_edit_dialog():
            data = request.form.to_dict()
            data_query = dict()
            data_query['id'] = int(data['id'])
            data_query['user_name'] = data['name']
            data_query['user_alias'] = data['alias']
            data_query['user_address'] = data['address']
            data_query['user_phone'] = int(data['phone'])
            if data['phone_2'] not in ['', 'None']:
                data_query['user_phone_2'] = int(data['phone_2'])
            else:
                data_query['user_phone_2'] = None
            data_query['user_city'] = data['city']
            db_resp = db_utils.add_new_customer(**data_query)
            if db_resp['code'] == 200:
                data_query_guarantor = {}
                data_query_guarantor['guarantor_1_name'] = data['guarantor_1_name']
                data_query_guarantor['guarantor_1_phone'] = data['guarantor_1_phone']
                data_query_guarantor['guarantor_1_address'] = data['guarantor_1_address']
                data_query_guarantor['guarantor_2_name'] = data['guarantor_2_name']
                data_query_guarantor['guarantor_2_phone'] = data['guarantor_2_phone']
                data_query_guarantor['guarantor_2_address'] = data['guarantor_2_address']
                db_resp = db_utils.update_guarantor_details(user_id=data_query['id'], loan_id=int(data['loan_id']),
                                                            data_query=data_query_guarantor)

            return db_resp


        @app.route('/api/hafta/customeredit_account', methods=['POST', 'GET'])
        def customeredit_account():
            data = request.form.to_dict()
            data_query = dict()
            data_query['id'] = int(data['id'])
            data_query['user_name'] = data['name']
            data_query['user_alias'] = data['alias']
            data_query['user_address'] = data['address']
            data_query['user_phone'] = int(data['phone'])
            data_query['user_city'] = data['city']
            db_resp = db_utils.add_new_customer(**data_query)
            return db_resp


        @app.route('/api/hafta/extend_hafta', methods=['POST', 'GET'])
        def extend_hafta():
            user_data = dict()

            if request.method == "POST":
                user_data['customer_id'] = int(request.form['user_id'])
                user_data['loan_id'] = int(request.form['loan_id'])
                user_data['amount'] = float(request.form['amount'])
                user_data['no_of_hafta'] = int(request.form['months'])
            else:
                user_data['customer_id'] = int(request.args['user_id'])
                user_data['loan_id'] = int(request.args['loan_id'])
                user_data['amount'] = float(request.args['amount'])
                user_data['no_of_hafta'] = int(request.args['months'])
            print(user_data)
            if db_utils.get_loan_type_by_loan_id(loan_id=user_data['loan_id']) == 'hafta':
                return {'code': 500, 'status': 'Loan must be Flat'}
            resp = db_utils.extend_hafta(**user_data)
            return resp

        @app.route('/api/hafta/extend_hafta_page', methods=['POST', 'GET'])
        def extend_hafta_page():
            data = get_users_details()
            return render_template('template/demo/vertical-default-dark/pages/addHafta.html', data=data)



        @app.route('/api/hafta/party_to_party_transfer', methods=['POST', 'GET'])
        def party_to_party_transfer():
            return None


        @app.route('/api/hafta/add_collection_dialog', methods=['POST', 'GET'])
        def add_collection_dialog():
            if request.method == "POST":

                if 'user_id' in request.form.to_dict().keys():
                    user_id = int(request.form['user_id'])
                    data = src.utils.get_user_details(int(request.form['user_id']))
                else:
                    data = src.utils.get_user_data_by_loan_id(int(request.form['loan_id']))
                    user_id = db_utils.get_user_id_from_loan_id(int(request.form['loan_id']))
            else:

                if 'user_id' in request.args.to_dict().keys():
                    user_id = int(request.args['user_id'])
                    data = src.utils.get_user_details(int(request.args['user_id']))
                else:
                    data = src.utils.get_user_data_by_loan_id(int(request.args['loan_id']))
                    user_id = db_utils.get_user_id_from_loan_id(int(request.args['loan_id']))
            data_ret = {'data': data, 'date_today': datetime.now().date(),
                        'total_pending_amount': get_user_pending_amount(user_id),
                        'total_due_amount': get_user_due_amount(user_id)}

            print(data_ret['total_pending_amount'])
            return render_template('templates/user_add_collection.html', data=data_ret)


        @app.route('/api/hafta/add_collection', methods=['POST', 'GET'])
        def add_collection():
            db_data = dict()
            db_data['id'] = int(request.form['user_id'])
            db_data['transaction_id'] = int(request.form['loan_id'])
            db_data['installment_num'] = int(request.form['no_of_installment'])
            db_data['paid_date'] = datetime.strptime(request.form['paid_date'], '%d/%m/%Y')
            db_data['paid_amount'] = float(request.form['paid_amount'])
            db_data['emi_amount'] = float(request.form['base_amount'])
            resp = db_utils.add_installment(**db_data)
            return resp


        @app.route('/api/hafta/close_loan_dialog', methods=['POST', 'GET'])
        def close_loan_dialog():
            if request.method == 'POST':
                data = src.utils.get_loan_entries_by_user_id(request.form['user_id'])
            else:
                data = src.utils.get_loan_entries_by_user_id(request.args['user_id'])
            return render_template('template/demo/vertical-default-dark/pages/closeLoan.html', data=data)


        @app.route('/api/hafta/close_loan', methods=['POST', 'GET'])
        def close_loan():
            resp = db_utils.close_loan(int(request.form['user_id']), int(request.form['loan_id']),
                                       float(request.form['amount']))
            print(resp)
            return resp


        ############### ACCOUNT ###############

        account_type = 'new'


        @app.route('/api/account', methods=['POST', 'GET'])
        def account():
            if session.get('username'):
                data = db_utils.get_users_details(user_type="account")
                today = datetime.now().strftime("%A, %d %B, %Y")
                return render_template('template/demo/vertical-default-dark/pages/AccountOnBoard1.html', data=data, today=today)
            else:
                return redirect('/api/user/login')


        @app.route('/api/account/fetch_customers', methods=['POST', 'GET'])
        def fetch_customers():
            return None


        @app.route('/api/account/current_user_account_entry_dialog', methods=['POST', 'GET'])
        def current_user_account_entry_dialog(id=None):
            data = src.utils.get_user_details(request.form['user_id'])
            try:
                resp = f"""
                    <html>
                    <head> 
                    <title>HTML Redirect</title>  
                    </head> 
                    <body>
                    <form action="/api/account/current_user_account_entry" method=POST></br>
                    <input type=text name=id value={request.form['user_id']}></br>
                    <input type=text name=name value={data[0]['user_name']} placeholder=Name></br>
                    <input type=text name=alias value={data[0]['user_name']} placeholder=Alias></br>
                    <input type=text name=address value={data[0]['user_address']} placeholder=Address></br>
                    <input type=text name=phone value={data[0]['user_phone']} placeholder=Phone></br>
                    <input type=text name=city value={data[0]['user_city']} placeholder=City></br>
                    <input type=text name=base_amount placeholder=BaseAmount></br>
                    <input type=text name=interest placeholder=Interest></br>
                    <input type=text name=noi placeholder=Installations></br>
                    <input type=date name=startdate value={datetime.now().date()} placeholder=StartDate></br>
                    <input type=text name=period placeholder=Period value=monthly></br>
                    <select id="cars" name=loan_type>
                      <option value="flat">Flat</option>
                      <option value="hafta">Hafta</option>
                    </select>
                    <input type=text name=paid_amount placeholder=Paid_amount></br>
                    <input type=submit value=Submit>
                    </form>
                    </body>
                    </html>"""
            except Exception as e:
                print(e)
            print(resp)
            return resp


        @app.route('/api/account/get_account_user_details_credit_debit', methods=['POST', 'GET'])
        def get_account_user_details_credit_debit():
            if request.method == 'POST':
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()
            if data['lenar'] not in ['C', 'CA', 'CAS', 'CASH']:
                lenar_user_loan_id = data['lenar'].split(' - ')[0]
                lenar_user_loan_id = int(lenar_user_loan_id) if lenar_user_loan_id.isnumeric() else lenar_user_loan_id
                lenar_user_user_id = get_user_id_from_loan_id(lenar_user_loan_id, loan_type='account')
            else:
                lenar_user_user_id = data['lenar']
            return str(db_utils.get_account_user_pending_amount(lenar_user_user_id))


        @app.route('/api/account/extend_hafta', methods=['POST', 'GET'])
        def account_extend_hafta():
            user_data = dict()
            user_data['customer_id'] = int(request.form['user_id'])
            user_data['loan_id'] = int(request.form['loan_id'])
            user_data['amount'] = float(request.form['amount'])
            user_data['no_of_hafta'] = int(request.form['months'])
            resp = db_utils.extend_hafta(user_type="account", **user_data)
            return str(resp)




        @app.route('/api/account/new_account_entry_dialog', methods=['POST', 'GET'])
        def new_account_entry_dialog(id=None):
            if not session.get('username'):
                # TODO : code to close current dialog and open login screen in mainwindow
                return "logged out"
            max_id = db_utils.get_max_customer_id(id)
            data = {'max_id': max_id, 'today': datetime.now().date()}
            return render_template("template/demo/vertical-default-dark/pages/addNewAccount.html", data=data)


        @app.route('/api/account/current_user_account_entry', methods=['POST', 'GET'])
        def current_user_account_entry():
            return new_account_entry(current_user=True)


        @app.route('/api/account/add_new_account_customer', methods=['POST', 'GET'])
        def add_new_account_customer():
            data = request.form.to_dict()
            data_query = dict()
            data_query['id'] = data['id']
            data_query['user_name'] = data['name']
            data_query['user_alias'] = data['alias']
            data_query['user_address'] = data['address']
            data_query['user_phone'] = data['phone']
            data_query['user_city'] = data['city']
            db_resp = db_utils.add_new_customer(**data_query)
            return db_resp


        @app.route('/api/account/new_account_entry', methods=['POST', 'GET'])
        def new_account_entry(current_user=False):
            if not is_logged_in():
                # TODO : code to close current dialog and open login screen in mainwindow
                return "logged out"
            data = request.form.to_dict()
            if not current_user:
                resp = add_new_customer()
            else:
                resp = {'code': 200}
            entry_added_flag = False
            try:
                if resp['code'] == 200:
                    resp = create_entry_new_hafta(user_type="account", **data)
                    if resp['code'] == 200:
                        entry_added_flag = True
            except Exception as e:
                print(e)
                return {'code': 500, 'status': 'server error occured'}

            if entry_added_flag:
                return {'code': 200, 'status': 'user added with hafta'}

            return resp


        @app.route('/api/account/account_hafta_extend_dialog', methods=['POST', 'GET'])
        def account_hafta_extend_dialog():
            if request.method == "POST":
                data = src.utils.get_user_details(request.form['user_id'], user_type='account')
            else:
                data = src.utils.get_user_details(request.args['user_id'], user_type='account')
            loan_id_list = []
            # for d in data:
            #     if d['loan_id'] is None:
            #         continue
            #     if d['loan_id'] in loan_id_list:
            #         continue
            #     else:
            #         loan_id_list.append(d['loan_id'])
            credit_amt = 0
            debit_amt = 0
            for val in data:
                if val['tx_type'] == 'cr':
                    credit_amt += val['amount']
                else:
                    debit_amt += val['amount']
            data_rander = {'data': data, 'loan_id_list': loan_id_list, 'date_today': datetime.now().date(),
                           'credit_amt': credit_amt, 'debit_amt': debit_amt}
            return render_template('template/demo/vertical-default-dark/pages/partyInfoAccount.html', data=data_rander)


        @app.route('/api/account/pay_dialog', methods=['POST', 'GET'])
        def pay_dialog():
            return None


        @app.route('/api/account/customer_detail_dialog', methods=['POST', 'GET'])
        def customer_detail_dialog():
            return None


        @app.route('/api/account/pay_installment', methods=['POST', 'GET'])
        def pay_installment():
            return None


        @app.route('/api/account/add_collection_dialog', methods=['POST', 'GET'])
        def add_account_collection_dialog():
            if request.method == "POST":
                data = src.utils.get_user_details(int(request.form['user_id']), user_type="account")
            else:
                data = src.utils.get_user_details(int(request.args['user_id']), user_type="account")

            data_ret = {}
            data_ret['data'] = data
            data_ret['date_today'] = datetime.now().date()
            return render_template('templates/user_add_collection_account.html', data=data_ret)


        @app.route('/api/account/add_collection_new', methods=['POST', 'GET'])
        def add_collection_new():
            if request.method == 'POST':
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()

            return db_utils.add_account_entry(data)


        @app.route('/api/account/add_collection', methods=['POST', 'GET'])
        def add_account_collection():
            db_data = dict()
            if request.method == 'POST':
                db_data['id'] = int(request.form['user_id'])
                db_data['transaction_id'] = int(request.form['loan_id'])
                db_data['installment_num'] = int(request.form['no_of_installment'])
                db_data['paid_date'] = datetime.strptime(request.form['paid_date'], '%d/%m/%Y')
                db_data['paid_amount'] = float(request.form['paid_amount'])
                db_data['emi_amount'] = float(request.form['base_amount'])
            else:
                db_data['id'] = int(request.args['user_id'])
                db_data['transaction_id'] = int(request.args['loan_id'])
                db_data['installment_num'] = int(request.args['no_of_installment'])
                db_data['paid_date'] = datetime.strptime(request.args['paid_date'], '%d/%m/%Y')
                db_data['paid_amount'] = float(request.args['paid_amount'])
                db_data['emi_amount'] = float(request.args['base_amount'])

            resp = db_utils.add_installment(**db_data, user_type="account")
            return resp


        @app.route('/api/account/close_loan_dialog', methods=['POST', 'GET'])
        def close_account_loan_dialog():
            if request.method == 'POST':
                data = src.utils.get_loan_entries_by_user_id(int(request.form['user_id']), user_type="account")
            else:
                data = src.utils.get_loan_entries_by_user_id(int(request.args['user_id']), user_type="account")
            return render_template('templates/close_account_loan.html', data=data, user_type="account")


        @app.route('/api/account/close_loan', methods=['POST', 'GET'])
        def close_account_loan():
            resp = db_utils.close_loan(int(request.form['user_id']), int(request.form['loan_id']),
                                       float(request.form['amount']), user_type="account")
            print(resp)
            return resp


        @app.route('/api/account/credit_debit_amount', methods=['POST', 'GET'])
        def credit_debit_amount():
            if request.method == 'POST':
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()

            lenar_user_loan_id = data['lenar'].split(' - ')[0]
            denar_user_loan_id = data['denar'].split(' - ')[0]
            lenar_user_loan_id = int(lenar_user_loan_id) if lenar_user_loan_id.isnumeric() else lenar_user_loan_id
            denar_user_loan_id = int(denar_user_loan_id) if denar_user_loan_id.isnumeric() else denar_user_loan_id
            amount = float(data['amount'])
            remark = data['remark']
            if lenar_user_loan_id not in ['C', 'CA', 'CAS', 'CASH']:
                lenar_user_user_id = get_user_id_from_loan_id(lenar_user_loan_id, loan_type='account')
            else:
                lenar_user_user_id = lenar_user_loan_id
            if denar_user_loan_id not in ['C', 'CA', 'CAS', 'CASH']:
                denar_user_user_id = get_user_id_from_loan_id(denar_user_loan_id, loan_type='account')
            else:
                denar_user_user_id = denar_user_loan_id
            if lenar_user_user_id != 'CASH' and denar_user_user_id != 'CASH':
                return {'code': 500, 'status': 'Lenar or Denar should be CASH'}
            elif lenar_user_user_id == 'CASH' and denar_user_user_id == 'CASH':
                return {'code': 500, 'status': 'Lenar and Denar both sould not be CASH'}
            else:
                try:
                    return db_utils.add_account_entry_by_lenar_denar(lenar_user_user_id, denar_user_user_id, amount,
                                                                     remark, data['date'])
                except Exception as e:
                    print('credit_debit_amount', e)
                    return {'code': 500, 'status': 'something occured wrong'}


        ######### Debit Accounts ###################################################################################
        @app.route('/api/debit_account', methods=['GET', 'POST'])
        def debit_accounts():
            data = db_utils.get_users_details(user_type='account')
            user_list = ['CASH']
            for d in data:
                user_list.append(str(d['loan_id']) + " - " + str(d['user_name']))
            return render_template('template/demo/vertical-default-dark/pages/creditDebitAccount1.html', data=user_list,
                                                               date_today=datetime.now().date(), today=datetime.now().strftime("%A, %d %B, %Y"))


        @app.route('/api/hafta/add_collection_user_info', methods=['GET', 'POST'])
        def add_collection_user_info():
            if request.method == 'POST':
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()
            user_data = db_utils.get_user_data_by_loan_id(loan_id=int(data['lenar'].split(' - ')[0]))
            df = pd.DataFrame(columns=['Id', 'Date', 'Amount', 'Status'])
            for val in user_data:

                row = pd.Series(
                    [val['no_of_installment'], val['date_to_pay'], val['emi_amount'], val['tx_status']],
                    ['Id', 'Date', 'Amount', 'Status'])
                print(val['date_to_pay'].date(), val['no_of_installment'])
                df = df.append(row, ignore_index=True)

            df = df.sort_values(by='Id', ascending=True)
            print(df)
            for i, val in enumerate(df['Date']):
                print(val, df['Date'].iloc[i])
                if type(val) == str:
                    df['Date'].iloc[i] = datetime.strptime(val, "%d/%m/%Y")
                try:
                    df['Date'].iloc[i] = val.strftime("%d/%m/%Y")
                except Exception as e:
                    df['Date'].iloc[i] = val
            user_id = get_user_id_from_loan_id(int(data['lenar'].split(' - ')[0]))
            value = df.iloc[np.where(df['Status'] == 0)[0][0]]['Amount']
            emi_no = df.iloc[np.where(df['Status'] == 0)[0][0]]['Id']
            cash_amount = db_utils.get_amount_value_from_general(session.get('username'))
            df['Status'].replace({1: 'Paid', 0: 'Pending'}, inplace=True)
            name = str(data['lenar'].split(' - ')[0]) + " - " + Customer.query.filter_by(id=user_id).first().user_name
            return {'table': create_html_table(df, show_col_name=True), 'value': value, 'emi_no': emi_no, 'cash_amount':
                    cash_amount, 'user_id': user_id, 'name': name}


        @app.route('/api/hafta/add_collection_dialog_new', methods=['GET', 'POST'])
        def add_collection_dialog_new():
            data = db_utils.get_users_details(user_type='loan')
            user_list = []
            for d in data:
                try:
                    user_list.append(str(d['loan_id']) + " - " + str(d['user_name']))
                except Exception as e:
                    continue
            return render_template('template/demo/vertical-default-dark/pages/addCollections1.html', data=user_list,
                                                               date_today=datetime.now().date(), today=datetime.now().strftime("%A, %d %B, %Y"))


        @app.route('/api/debit_account/add_new', methods=['post', 'get'])
        def debit_add_new():
            if request.method == "GET":
                data = src.utils.get_user_details(request.args['user_id'], account_type='debit')
            else:
                data = src.utils.get_user_details(request.form['user_id'], account_type='debit')
            loan_id_list = []
            data_rander = {'data': data, 'loan_id_list': loan_id_list}
            return render_template('templates/new_extend_form_debit.html', data=data_rander)


        @app.route('/api/debit/current_user_debit_entry_dialog', methods=['POST', 'GET'])
        def current_user_debit_entry_dialog(id=None):
            if request.method == "POST":
                data = src.utils.get_user_details(request.form['user_id'], account_type='debit')
                data = data[0]
                request_data = request.form.to_dict()
                data['max_id'] = request.form['user_id']
            else:
                data = src.utils.get_user_details(int(request.args['user_id']), account_type='debit')
                data = data[0]
                request_data = request.args.to_dict()
                data['max_id'] = request.args['user_id']
            try:
                resp = render_template('templates/usermain_debit.html', data=data)
            except Exception as e:
                print(e)
            return resp


        @app.route('/api/debit/current_user_hafta_entry', methods=['POST', 'GET'])
        def current_user_debit_entry():
            return new_hafta_entry(current_user=True)


        ###############Profile####################
        @app.route('/api/profile', methods=['GET', 'POST'])
        def profile_accounts():
            data = db_utils.finance_user_details()
            data['msg'] = ""
            data['today']=datetime.now().strftime("%A, %d %B, %Y")
            return render_template('template/demo/vertical-default-dark/pages/settings1.html', data=data)


        @app.route('/api/update_profile', methods=['POST', 'GET'])
        def update_profile():
            if request.method == "POST":
                request_data = request.form.to_dict()
            else:
                request_data = request.args.to_dict()
            if request_data['old_password'] == '':
                return {'code': 500, "status": "Please enter Current password"}
            elif db_utils.login(session.get('username'), request_data['old_password'])['code'] == 200:
                del request_data['old_password']
                if request_data['new_password'] == '':
                    del request_data['new_password']
                else:
                    request_data['password'] = md5(request_data['new_password'].encode()).hexdigest()
                    del request_data['new_password']
                resp = db_utils.update_finance_user(**request_data)
                return resp
            else:
                return {'code': 500, "status": "Invalid password"}


        ########## REPORT ############
        @app.route('/api/report', methods=['POST', 'GET'])
        def report():
            data = get_users_details(loan_status='both')
            account_data = get_users_details(user_type='account')
            return render_template('template/demo/vertical-default-dark/pages/report1.html', data=data,
                                                               account_data=account_data, today=datetime.now().strftime("%A, %d %B, %Y"))


        @app.route('/api/report/pending_installment_by_date', methods=['POST', 'GET'])
        def pending_installment_by_date():
            try:
                if request.method == "POST":
                    request_data = request.form.to_dict()
                else:
                    request_data = request.args.to_dict()
                emis = src.utils.get_report_of_pending_installments_by_date(
                    datetime.strptime(str(request_data['date']), "%Y-%m-%d"))
                emis.index = np.arange(1, len(emis) + 1)
                emis = emis.sort_values(by='Date')
                table = create_html_table(emis)
                # emis.index.rename('id', inplace=True)
                return render_template("templates/report_page_table.html",
                                       data={'table': Markup(table),
                                             'name': 'Pending Installments by Date'})
            except:
                if not path.exists('logs.txt'):
                    with open('logs.txt', 'w+') as file:
                        file.writelines('logs')
                with open('logs.txt', 'w+') as file:
                    traceback.print_exc(file=file)


        @app.route('/api/report/user_entries_between_date', methods=['POST', 'GET'])
        def user_entries_between_date():
            if request.method == "POST":
                request_data = request.form.to_dict()
            else:
                request_data = request.args.to_dict()
            # report = src.utils.get_user_entries_between_date(int(request_data['user_id']),
            #                                                  datetime.strptime(str(request_data['from_date']),
            #                                                                             "%d/%m/%Y"),
            #                                                  datetime.strptime(str(request_data['to_date']),
            #                                                                             "%d/%m/%Y"))
            report = db_utils.get_user_entries_report(int(request_data['user_id']))
            report.index = np.arange(1, len(report) + 1)
            report.index.name = "id"

            return render_template("templates/report_page_table.html",
                                   data={'table': Markup(create_html_table(report)),
                                         'name': 'User Entries'})


        # @app.route('/api/report/general_report', methods=['POST', 'GET']) def day_report(): if request.method ==
        # 'POST': request_data = request.form.to_dict() else: request_data = request.args.to_dict() df,
        # total_collections = db_utils.get_day_wise_installments( datetime.strptime(str(request_data[
        # 'date']), "%d/%m/%Y")) return render_template("templates/report_page_table.html", data={'table': Markup(
        # df.to_html(header=False, index=False)), 'name': 'Day Report'})
        @app.route('/api/get_guarantor_details_by_loan_id', methods=['POST', 'GET'])
        def get_guarantor_details_by_loan_id():
            if request.method == "POST":
                user_id = request.form.get('user_id')
                loan_id = request.form.get('loan_id')
            else:
                user_id = request.args.get('user_id')
                loan_id = request.args.get('loan_id')

            data = db_utils.get_guarantor_details_by_loan_id(user_id, loan_id)
            data_ret = {'code': 200, 'data': data}
            return data_ret


        @app.route('/api/report/user_pending_installments', methods=['POST', 'GET'])
        def user_pending_installments():
            if request.method == 'POST':
                request_data = request.form.to_dict()
            else:
                request_data = request.args.to_dict()
            _, data = db_utils.get_pending_installments_of_user(int(request_data['user_id']),
                                                                datetime.strptime(
                                                                    str(request_data['date']), "%Y-%m-%d"))
            columns = ['User ID', 'Loan ID', 'Installment ID', 'Amount', 'Date to Pay']
            df = pd.DataFrame(columns=columns)
            for val in data:
                row = pd.Series(
                    [int(request_data['user_id']), val['loan_id'], val['no_of_installment'], val['emi_amount'],
                     val['date_to_pay']], columns)
                df = df.append(row, ignore_index=True)
            return render_template("templates/report_page_table.html", data={'table': Markup(create_html_table(df)),
                                                                             'name': 'Pending '
                                                                                     'Installments'})


        @app.route('/api/report/account_user_pending_installments', methods=['POST', 'GET'])
        def account_user_pending_installments():
            if request.method == 'POST':
                request_data = request.form.to_dict()
            else:
                request_data = request.args.to_dict()

            denar_user_user_id = int(request_data['user_id'])
            data = db_utils.get_account_user_entries(denar_user_user_id,
                                                     datetime.strptime(str(request_data['from_date']),
                                                                       "%Y-%m-%d") if str(request_data[
                                                                                              'from_date']) != '' else datetime.now().date() - relativedelta(
                                                         months=1),
                                                     datetime.strptime(
                                                         str(request_data['date']), "%Y-%m-%d") if str(
                                                         request_data['date']) != '' else datetime.now().date())

            return render_template("templates/report_page_table.html", data={'table': Markup(data),
                                                                             'name': 'Account Entries'})


        @app.route('/api/report/day_report', methods=['POST', 'GET'])
        def day_report():
            if request.method == 'POST':
                date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            else:
                date = datetime.strptime(request.args['date'], '%Y-%m-%d').date()
            data = db_utils.get_daily_report_by_date(date)
            credit_cols = data['credit_transactions'].columns.values.tolist()
            debit_cols = data['debit_transactions'].columns.values.tolist()
            for col in ['tx_id', 'party_id', 'account_type', 'status', 'total_balance',
                        'tx_date']:
                if col in credit_cols:
                    del data['credit_transactions'][col]
                if col in debit_cols:
                    del data['debit_transactions'][col]
            data['debit_transactions'] = data['debit_transactions'].reindex(
                ['loan_id', 'name', 'amount'], axis=1)
            data['credit_transactions'] = data['credit_transactions'].reindex(
                ['loan_id', 'name', 'amount'], axis=1)

            return render_template("templates/general_report_page.html",
                                   data={'table1': Markup(create_html_table(data['credit_transactions'])),
                                         # data.to_html(header=False, index=False)),
                                         'table2': Markup(create_html_table(data['debit_transactions']))})


        @app.route('/api/report/general_report', methods=['POST', 'GET'])
        def general_report():
            general_reports = db_utils.get_general_report()
            return render_template("templates/general_report_page.html",
                                   data={'table1': Markup(general_reports['general']), 'table2':
                                       Markup(general_reports['all_transaction'])})


        def run_flask_server():
            app.run()


        class AnotherWindow(QWidget):
            """
            This "window" is a QWidget. If it has no parent, it
            will appear as a free-floating window as we want.
            """

            def __init__(self, url, data):
                super().__init__()
                layout = QVBoxLayout()
                self.setGeometry(0, 0, 1300, 700)
                self.browser = QWebEngineView(self)
                self.setWindowTitle(url.split("/")[-2] + " | BlackQR")
                doc_flag = False
                if 'doc_flag' in data.keys():
                    doc_flag = True
                    del data['doc_flag']
                if data:
                    url_param = '&'.join(["{}={}".format(k, v) for k, v in data.items()])
                    url_f = url + "?" + url_param
                else:
                    url_f = url
                self.browser.setUrl(QUrl(url_f))
                self.browser.setContextMenuPolicy(Qt.NoContextMenu)
                layout.addWidget(self.browser)
                self.setLayout(layout)
                if doc_flag:
                    self.export_button = QPushButton(self)
                    self.export_button.move(30, 30)
                    self.browser.move(0, 40)
                    self.export_button.setText("Export")
                    file_name = path.join("Documents", url.split("/")[-1] + strftime("%Y%m%d-%H%M%S") + ".pdf")
                    loader = QtWebEngineWidgets.QWebEngineView()
                    loader.setZoomFactor(1)
                    loader.page().pdfPrintingFinished.connect(
                        lambda *args: print('finished:', args))
                    loader.load(QUrl(url_f))

                    def emit_pdf(finished):
                        loader.page().printToPdf(file_name)
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)

                        msg.setText("File Downloaded")
                        msg.setInformativeText("File Downloaded to " + file_name)
                        msg.setStandardButtons(QMessageBox.Ok)

                        def msgbtn():
                            msg.close()
                            # startfile(file_name)

                        msg.buttonClicked.connect(msgbtn)

                        msg.exec_()

                    self.export_button.clicked.connect(emit_pdf)


        class MainWindow(QMainWindow):

            def __init__(self):
                super().__init__()
                layout = QVBoxLayout()
                self.setGeometry(0, 0, 900, 900)
                self.browser = QWebEngineView(self)
                self.showMaximized()
                self.setWindowTitle("Finance Software | BlackQR")
                self.browser.setUrl(QUrl("http://127.0.0.1:5000"))
                self.browser.setContextMenuPolicy(Qt.NoContextMenu)
                layout.addWidget(self.browser)

                self.setCentralWidget(self.browser)
                self.setLayout(layout)
                self.w = []

            def show_new_window(self, url, data):
                self.wa = AnotherWindow(url=url, data=data)
                self.w.append(self.wa)
                self.wa.show()


        if __name__ == '__main__':
            app_ = QApplication(argv)
            app_.setWindowIcon(QIcon('icon.ico'))
            window = MainWindow()
            window.show()
            Thread(target=run_flask_server, daemon=True).start()
            app_.exec_()
            #backup
            backup_path = path.abspath('..')
            copy(f'{config.db_name}.dll', backup_path)
            # run_flask_server()
