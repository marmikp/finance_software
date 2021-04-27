import datetime
import sys
from functools import partial
from random import random, randint

import pandas as pd
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton, QAction
from PyQt5.uic.uiparser import QtWidgets
from flask import Flask, request, render_template, session, redirect
from furl import furl
from markupsafe import Markup
from sqlalchemy import MetaData

import src.utils
from database import db_utils, model
from database.db_utils import get_user_data, get_users_details
from database.model import db
from src import utils
from src.utils import is_logged_in, create_entry_new_hafta
from pyfladesk import init_gui
import threading
from qt_thread_updater import get_updater

app = Flask(__name__, template_folder='web', static_folder='web')
app.secret_key = '123456'
app.config['SESSION_TYPE'] = 'filesystem'
model.init_database(app)
with app.app_context():
    db_utils.META_DATA = MetaData(bind=db.session.get_bind(), reflect=True)


@app.route("/api/test", methods=['POST', 'GET'])
def test():
    try:
        request_data = request.form.to_dict()
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


######## GENERAL ########
@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get('username'):
        return render_template('index.html')
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
            return render_template('login.html', data="invalid username or password")
    else:

        return render_template('login.html')


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
    db_resp = db_utils.add_new_customer(**data_query)
    return db_resp


############## HAFTA ##############
@app.route('/api/hafta', methods=['GET', 'POST'])
def hafta():
    if session.get('username'):
        data = db_utils.get_users_details()
        return render_template('index.html', data=Markup(render_template('templates/user_form.html', data=data)))
    else:
        return redirect('/api/user/login')


@app.route('/api/hafta/new_hafta_entry_dialog', methods=['POST', 'GET'])
def new_hafta_entry_dialog(id=None):
    print(id)
    if not session.get('username'):
        # TODO : code to close current dialog and open login screen in mainwindow
        return "logged out"
    max_id = db_utils.get_max_customer_id(id)
    return f"""
    <html>
    <head> 
    <title>HTML Redirect</title>  
    </head> 
    <body>
    <form action="/api/hafta/new_hafta_entry" method=POST></br>
    <input type=text name=id value={max_id}></br>
    <input type=text name=name placeholder=Name></br>
    <input type=text name=alias placeholder=Alias></br>
    <input type=text name=address placeholder=Address></br>
    <input type=text name=phone placeholder=Phone></br>
    <input type=text name=city placeholder=City></br>
    <input type=text name=base_amount placeholder=BaseAmount></br>
    <input type=text name=interest placeholder=Interest></br>
    <input type=text name=noi placeholder=Installations></br>
    <input type=date name=startdate placeholder=StartDate></br>
    <input type=text name=period placeholder=Period value=monthly></br>
    <select id="cars" name=loan_type>
      <option value="flat">Flat</option>
      <option value="hafta">Hafta</option>
    </select>
    Is Debit account: <input type='checkbox' name="is_debit"></br>
    <input type=text name=guarantor_1_name placeholder=guarantor_1_name></br>
    <input type=text name=guarantor_1_phone placeholder=guarantor_1_phone></br>
    <input type=text name=guarantor_1_address placeholder=guarantor_1_address></br>
    <input type=text name=guarantor_2_name placeholder=guarantor_2_name></br>
    <input type=text name=guarantor_2_phone placeholder=guarantor_2_phone></br>
    <input type=text name=guarantor_2_address placeholder=guarantor_2_address></br>
    <input type=text name=paid_amount placeholder=Paid_amount></br>
    <input type=textarea name='remark' placeholder='Remark'></br>
    <input type=submit value=Submit>
    </form>
    </body>
    </html>"""


@app.route('/api/hafta/current_user_hafta_entry_dialog', methods=['POST', 'GET'])
def current_user_hafta_entry_dialog(id=None):
    print(request.form['user_id'])
    data = src.utils.get_user_details(request.form['user_id'])
    try:
        resp = f"""
            <html>
            <head> 
            <title>HTML Redirect</title>  
            </head> 
            <body>
            <form action="/api/hafta/new_hafta_entry" method=POST></br>
            <input type=text name=id value={request.form['user_id']}></br>
            <input type=text name=name value={data[0]['user_name']} placeholder=Name></br>
            <input type=text name=alias value={data[0]['user_name']} placeholder=Alias></br>
            <input type=text name=address value={data[0]['user_address']} placeholder=Address></br>
            <input type=text name=phone value={data[0]['user_phone']} placeholder=Phone></br>
            <input type=text name=city value={data[0]['user_city']} placeholder=City></br>
            <input type=text name=base_amount placeholder=BaseAmount></br>
            <input type=text name=interest placeholder=Interest></br>
            <input type=text name=noi placeholder=Installations></br>
            <input type=date name=startdate value={datetime.datetime.now().date()} placeholder=StartDate></br>
            <input type=text name=period placeholder=Period value=monthly></br>
            <select id="cars" name=loan_type>
              <option value="flat">Flat</option>
              <option value="hafta">Hafta</option>
            </select>
            <input type=text name=guarantor_1_name placeholder=guarantor_1_name></br>
            <input type=text name=guarantor_1_phone placeholder=guarantor_1_phone></br>
            <input type=text name=guarantor_1_address placeholder=guarantor_1_address></br>
            <input type=text name=guarantor_2_name placeholder=guarantor_2_name></br>
            <input type=text name=guarantor_2_phone placeholder=guarantor_2_phone></br>
            <input type=text name=guarantor_2_address placeholder=guarantor_2_address></br>
            <input type=text name=paid_amount placeholder=Paid_amount></br>
            
            <input type=submit value=Submit>
            </form>
            </body>
            </html>"""
    except Exception as e:
        print(e)
    print(resp)
    return resp


@app.route('/api/hafta/current_user_hafta_entry', methods=['POST', 'GET'])
def current_user_hafta_entry():
    return new_hafta_entry(current_user=True)


@app.route('/api/hafta/new_hafta_entry', methods=['POST', 'GET'])
def new_hafta_entry(current_user=False):
    if not is_logged_in():
        # TODO : code to close current dialog and open login screen in mainwindow
        return "logged out"
    data = request.form.to_dict()
    if not current_user:
        resp = add_new_customer()
    entry_added_flag = False
    try:
        if resp['code'] == 200:
            if 'is_debit' in list(data.keys()):
                if data['is_debit'] != 'on':
                    resp = create_entry_new_hafta(**data)
                else:
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
        data = src.utils.get_user_details(request.form['user_id'])
    else:
        data = src.utils.get_user_details(request.args['user_id'])
    loan_id_list = []
    for d in data:
        if d['loan_id'] in loan_id_list:
            continue
        else:
            loan_id_list.append(d['loan_id'])
    data_rander = {'data': data, 'loan_id_list': loan_id_list}
    return render_template('templates/new_extend_form.html', data=data_rander)


@app.route('/api/hafta/extend_hafta', methods=['POST', 'GET'])
def extend_hafta():
    user_data = dict()
    user_data['customer_id'] = int(request.form['user_id'])
    user_data['loan_id'] = int(request.form['loan_id'])
    user_data['amount'] = float(request.form['amount'])
    user_data['no_of_hafta'] = int(request.form['months'])
    resp = db_utils.extend_hafta(**user_data)
    return resp


@app.route('/api/hafta/party_to_party_transfer', methods=['POST', 'GET'])
def party_to_party_transfer():
    return None


@app.route('/api/hafta/add_collection_dialog', methods=['POST', 'GET'])
def add_collection_dialog():
    if request.method == "POST":
        data = src.utils.get_user_details(int(request.form['user_id']))
    else:
        data = src.utils.get_user_details(int(request.args['user_id']))
    return render_template('templates/user_add_collection.html', data=data)


@app.route('/api/hafta/add_collection', methods=['POST', 'GET'])
def add_collection():
    db_data = dict()
    db_data['id'] = int(request.form['user_id'])
    db_data['transaction_id'] = int(request.form['loan_id'])
    db_data['installment_num'] = int(request.form['no_of_installment'])
    db_data['paid_date'] = datetime.datetime.strptime(request.form['paid_date'], '%Y-%m-%d')
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
    return render_template('templates/close_loan.html', data=data)


@app.route('/api/hafta/close_loan', methods=['POST', 'GET'])
def close_loan():
    resp = db_utils.close_loan(int(request.form['user_id']), int(request.form['loan_id']),
                               float(request.form['amount']))
    print(resp)
    return resp


############### ACCOUNT ###############
@app.route('/api/account', methods=['POST', 'GET'])
def account():
    if session.get('username'):
        data = db_utils.get_users_details(user_type="account")
        return render_template('index.html',
                               data=Markup(render_template('templates/user_form_account.html', data=data)))
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
            <input type=date name=startdate value={datetime.datetime.now().date()} placeholder=StartDate></br>
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
    return f"""
    <html>
    <head> 
    <title>HTML Redirect</title>  
    </head> 
    <body>
    <form action="/api/account/new_account_entry" method=POST></br>
    <input type=text name=id value={max_id}></br>
    <input type=text name=name placeholder=Name></br>
    <input type=text name=alias placeholder=Alias></br>
    <input type=text name=address placeholder=Address></br>
    <input type=text name=phone placeholder=Phone></br>
    <input type=text name=city placeholder=City></br>
    <input type=text name=base_amount placeholder=BaseAmount></br>
    <input type=text name=interest placeholder=Interest></br>
    <input type=text name=noi placeholder=Installations></br>
    <input type=date name=startdate placeholder=StartDate></br>
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
    data = src.utils.get_user_details(request.form['user_id'], user_type='account')
    loan_id_list = []
    for d in data:
        if d['loan_id'] is None:
            continue
        if d['loan_id'] in loan_id_list:
            continue
        else:
            loan_id_list.append(d['loan_id'])
    data_rander = {'data': data, 'loan_id_list': loan_id_list}
    return render_template('templates/new_extend_form_account.html', data=data_rander)


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
    return render_template('templates/user_add_collection_account.html', data=data)


@app.route('/api/account/add_collection', methods=['POST', 'GET'])
def add_account_collection():
    db_data = dict()
    db_data['id'] = int(request.form['user_id'])
    db_data['transaction_id'] = int(request.form['loan_id'])
    db_data['installment_num'] = int(request.form['no_of_installment'])
    db_data['paid_date'] = datetime.datetime.strptime(request.form['paid_date'], '%Y-%m-%d')
    db_data['paid_amount'] = float(request.form['paid_amount'])
    db_data['emi_amount'] = float(request.form['base_amount'])
    resp = db_utils.add_installment(**db_data, user_type="account")
    return resp


@app.route('/api/account/close_loan_dialog', methods=['POST', 'GET'])
def close_account_loan_dialog():
    if request.method == 'POST':
        data = src.utils.get_loan_entries_by_user_id(request.form['user_id'], user_type="account")
    else:
        data = src.utils.get_loan_entries_by_user_id(request.args['user_id'])
    return render_template('templates/close_account_loan.html', data=data, user_type="account")


@app.route('/api/account/close_loan', methods=['POST', 'GET'])
def close_account_loan():
    resp = db_utils.close_loan(int(request.form['user_id']), int(request.form['loan_id']),
                               float(request.form['amount']), user_type="account")
    print(resp)
    return resp


######### Debit Accounts ###################################################################################
@app.route('/api/debit_account', methods=['GET', 'POST'])
def debit_accounts():
    data = db_utils.get_users_details(user_type='debit')
    return render_template('index.html', data=Markup(render_template('templates/user_form_debit.html', data=data)))


@app.route('/api/debit_account/add_new', methods=['post', 'get'])
def debit_add_new():
    data = src.utils.get_user_details(request.form['user_id'], account_type='debit')
    loan_id_list = []
    for d in data:
        if d['loan_id'] in loan_id_list:
            continue
        else:
            loan_id_list.append(d['loan_id'])
    data_rander = {'data': data, 'loan_id_list': loan_id_list}
    return render_template('templates/new_extend_form.html', data=data_rander)


########## REPORT ############
@app.route('/api/report', methods=['POST', 'GET'])
def report():
    data = get_users_details(all_entries=True)
    return render_template('index.html', data=Markup(render_template('templates/report_page.html', data=data)))


@app.route('/api/report/pending_installment_by_date', methods=['POST', 'GET'])
def pending_installment_by_date():
    emis = src.utils.get_report_of_pending_installments_by_date(
        datetime.datetime.strptime(str(request.form['date']), "%Y-%m-%d"))
    return emis.to_html()


@app.route('/api/report/user_entries_between_date', methods=['POST', 'GET'])
def user_entries_between_date():
    report = src.utils.get_user_entries_between_date(int(request.form['user_id']),
                                                     datetime.datetime.strptime(str(request.form['from_date']),
                                                                                "%Y-%m-%d"),
                                                     datetime.datetime.strptime(str(request.form['to_date']),
                                                                                "%Y-%m-%d"))
    return report.to_html()


@app.route('/api/report/day_report', methods=['POST', 'GET'])
def day_report():
    df, total_collections = db_utils.get_day_wise_installments(
        datetime.datetime.strptime(str(request.form['date']), "%Y-%m-%d"))
    return df.to_html()


@app.route('/api/report/user_pending_installments', methods=['POST', 'GET'])
def user_pending_installments():
    print(request.form['user_id'], request.form['date'])
    _, data = db_utils.get_pending_installments_of_user(int(request.form['user_id']), datetime.datetime.strptime(
        str(request.form['date']), "%Y-%m-%d"))
    columns = ['User ID', 'Loan ID', 'Installment ID', 'Amount', 'Date to Pay']
    df = pd.DataFrame(columns=columns)
    for val in data:
        row = pd.Series([int(request.form['user_id']), val['loan_id'], val['no_of_installment'], val['emi_amount'],
                         val['date_to_pay']], columns)
        df = df.append(row, ignore_index=True)
    return df.to_html()


@app.route('/api/report/account_transactions', methods=['POST', 'GET'])
def account_transactions():
    return None


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
        self.setGeometry(0,0,700,700)
        # self.label = QLabel("Another Window % d" % randint(0,100))
        # layout.addWidget(self.label)
        self.browser = QWebEngineView(self)
        # self.browser.setPage(CustomWebEnginePage(self))
        # self.browser.setGeometry(0,0,700,700)
        if data:
            # f = furl('')
            # f.args = data
            url_param = '&'.join(["{}={}".format(k, v) for k, v in data.items()])
            url = url + "?" + url_param
        self.browser.setUrl(QUrl(url))
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)
        layout.addWidget(self.browser)

        # self.setCentralWidget(self.browser)
        self.setLayout(layout)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setGeometry(0, 0, 700, 700)
        # self.label = QLabel("Another Window % d" % randint(0,100))
        # layout.addWidget(self.label)
        self.browser = QWebEngineView(self)
        # self.browser.setPage(CustomWebEnginePage(self))
        # self.browser.setGeometry(0,0,700,700)
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
    app_ = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    threading.Thread(target=run_flask_server, daemon=True).start()
    app_.exec_()
    # run_flask_server()
