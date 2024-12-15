from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import random
import string
import re
import sqlite3
from datetime import datetime
import sys

app = Flask(__name__)
app.secret_key = 'secret_key'


@app.route('/')
def home():
    
    return render_template('home.html', response = 0)

@app.route('/login_info', methods = ['POST'])
def login_info():

    #response = session.get("http://127.0.0.1:5000")
    username = request.form.get('username')
    password = request.form.get('password')
    create_inital_table()
    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()
        row = cursor.execute("SELECT username, password FROM accounts")
        user_pass_info = row.fetchall()

    user_found = False
    password_found = False
    for i in user_pass_info:
        if username == i[0]:
            user_found = True
            if password == i[1]:
                password_found = True

    if password_found == True:
        
        connection = sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db")
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM accounts WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        connection.close()

        if "logged_in_users" not in session:
            session['logged_in_users'] = []
        if username not in session['logged_in_users']:
            session['logged_in_users'].append(username)
            session.modified = True
        
        return redirect(url_for('correct_info', user_id = user_id, transfer_response = 0))
    elif user_found == True:
        return render_template('home.html', response = 1, error_message = "Password is incorret.")
    else:
        return render_template('home.html', response = 1, error_message = "Cannot find this user.")
    
        
@app.route('/transfer', methods = ['POST'])
def transfer():

    transfer_target = request.form.get('transfer_target')
    transfer_amount = request.form.get('transfer_amount')
    current_user_id = request.form.get('current_user_id')

    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM accounts WHERE username = ?", (transfer_target,))
        transfer_target_result = cursor.fetchone()
        cursor.execute("SELECT username FROM accounts WHERE id = ?", (current_user_id,))
        current_username = cursor.fetchone()[0]
        transfer_response = 1

        if transfer_target_result != None:
            now = datetime.now()
            current_date = now.strftime("%B %d, %Y")
            cursor.execute("SELECT balance FROM accounts WHERE id = ?", (current_user_id,))
            current_target_balance = cursor.fetchone()[0]
            new_current_balance = int(current_target_balance) - int(transfer_amount)
            cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_current_balance, current_user_id))
            new_target_balance = int(transfer_amount) + int(transfer_target_result[0])
            cursor.execute("UPDATE accounts SET balance = ? WHERE username = ?", (new_target_balance, transfer_target))

            formatted_current_id = "_" + str(current_user_id)
            cursor.execute(f"INSERT INTO {formatted_current_id}(date, amount, sender, reciever) VALUES (?, ?, ?, ?)", (current_date, transfer_amount, current_username, transfer_target))

            cursor.execute("SELECT id FROM accounts WHERE username = ?", (transfer_target,))
            target_id = "_" + str(cursor.fetchall()[0][0])

            cursor.execute(f"INSERT INTO {target_id}(date, amount, sender, reciever) VALUES (?, ?, ?, ?)", (current_date, transfer_amount, current_username, transfer_target))
            transfer_response = 0

        return redirect(url_for('correct_info', user_id= current_user_id, transfer_response = transfer_response))

@app.route('/delete_account', methods = ['POST'])
def delete_account():

    user_id = request.form.get('current_user_id')
    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()
        formatted_id = '_'+ str(user_id)
        cursor.execute(f"DROP TABLE {formatted_id}")
        cursor.execute("SELECT username FROM accounts WHERE id = ?", (int(user_id),))
        username = cursor.fetchone()[0]
        cursor.execute("DELETE FROM accounts WHERE id = ?", (int(user_id),))
    
    return render_template("delete_account.html", username = username)


@app.route('/logout', methods = ['POST'])
def logout():

    user_id = request.form.get('current_user_id')
    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()   
        cursor.execute("SELECT username FROM accounts WHERE id = ?", (int(user_id),))
        username = cursor.fetchone()[0]
        print(f'usernamme: {username}')
        session["logged_in_users"].remove(username)
        session.modified = True

    return render_template("logout.html", username = username)
    


@app.route('/correct_info')
def correct_info():
    
    user_id = request.args.get('user_id')
    value = still_login_in(user_id)

    if value != True:
        return value

    transfer_response = request.args.get('transfer_response')
    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT balance, password, username FROM accounts WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        balance = result[0]
        password = result[1]
        username = result[2]
        formatted_id = "_" + str(user_id)
        cursor.execute(f"SELECT * FROM {formatted_id}")
        transaction_history = cursor.fetchall()
    return render_template("correct_info.html", username = username, password = password, balance = balance, transaction_history = transaction_history, user_id = user_id, transfer_response = transfer_response)
    
@app.route('/account_info', methods = ['GET'])
def account_info():

    user_id = request.args.get('current_user_id')
    data = get_data(user_id)
    return render_template("account_info.html", data = data)


def still_login_in(user_id):
    
    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()   
        cursor.execute("SELECT username FROM accounts WHERE id = ?", (user_id,))
        username = cursor.fetchone()[0]

    if "logged_in_users" not in session:
            session['logged_in_users'] = []
   
    if username not in session['logged_in_users']:  # Check if user is logged in
        return redirect(url_for('home'))
        
    return True

@app.route('/new_account')
def new_account():

    account_creation = request.args.get('account_creation')
    
    if account_creation == None:
        account_creation = ''
    
    states_and_territories = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
        "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
        "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
        "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", 
        "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", 
        "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", 
        "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", 
        "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
        "American Samoa", "Guam", "Northern Mariana Islands", "Puerto Rico", "U.S. Virgin Islands"]
    
    genders = ["Male", "Female"]

    return render_template("new_account.html", states_and_territories = states_and_territories, genders = genders, account_creation = account_creation)

@app.route('/create_account', methods = ['POST'])
def create_account():

    username = request.form.get('username')

    create_inital_table()

    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        
        cursor = connection.cursor() 
        
        row = cursor.execute("SELECT username FROM accounts")
        all_names = row.fetchall()
        
        duplicate_names = 0
        account_creation = 'Username is already taken.'
        for i in range(len(all_names)):
            if username == all_names[i][0]:
                duplicate_names = 1
                break

        if duplicate_names == 0:
            
            password = request.form.get('password')
            now = datetime.now()
            created_date = now.strftime("%B %d, %Y")            
            balance = request.form.get('balance')
            first_name = request.form.get('first_name')
            last_name =  request.form.get('last_name')
            city_town =  request.form.get('city_town')
            states_and_territories = request.form.get('states_and_territories')
            email_address = request.form.get('email_address')
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            address = request.form.get('address')

            #print(f"username: {username}")
            #print(f"password: {password}")
            #print(f"created_date: {created_date}")
            #print(f"balance: {balance}")
            #print(f"first name: {first_name}")
            #print(f"last name: {last_name}")
            #print(f"city_town: {city_town}")
            #print(f"states_and_territories: {states_and_territories}")
            #print(f"email_address: {email_address}")
            #print(f"date_of_birth: {date_of_birth}")
            #print(f"gender: {gender}")
            #print(f"address: {address}")

            cursor.execute("INSERT INTO accounts (username, password, created_date, balance, first_name, last_name, city_town, states_and_territories, email_address, date_of_birth, gender, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                 (username, password, created_date, balance, first_name, last_name, city_town, states_and_territories, email_address, date_of_birth, gender, address))
            
            cursor.execute("SELECT id FROM accounts WHERE username = ?", (username,))
            user_id = cursor.fetchone()[0]
            unique_id = "_" + str(user_id)
            
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {unique_id}(date, amount, sender, reciever)")
            cursor.execute(f"INSERT INTO {unique_id} (date, amount, sender, reciever) VALUES (?, ?, ?, ?)", (created_date, balance, "Deposit", "Deposit"))
            account_creation = 'Your account has succesfully been created.'
            
    return redirect(url_for("new_account", account_creation = account_creation))
        
    
def create_inital_table():

    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        balance REAL NOT NULL,
        address TEXT NOT NULL,
        created_date TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        city_town TEXT NOT NULL,
        states_and_territories TEXT NOT NULL,
        email_address TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
        gender TEXT NOT NULL)
        """)
        
def get_data(user_id):

    with sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (user_id,))
        info = cursor.fetchone()
        dict_info = {"id": info[0],
                    "username": info[1],
                     "password": info[2],
                     "balance": info[3],
                     "address": info[4],
                     "created_date": info[5],
                     "first_name": info[6], 
                     "last_name": info[7],
                     "city_town": info[8],
                     "states_and_territories": info[9],
                     "email_address": info[10],
                     "date_of_birth": info[11],
                     "gender": info[12]
        }
    return dict_info

def generate_examples(number):

    user_pass = list()

    for i in range(number):
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
        info_templates = f"Username: {username} Password: {password}\n" 
        user_pass.append(info_templates)

    with open(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\name_and_pass.txt", 'w') as f:
        for i in user_pass:
            f.write(i)

def print_all_data():

    connection = sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db")
    cursor = connection.cursor()


    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()  # Fetch all table names as a list of tuples
    print(tables)

    for table in tables:
        table_name = table[0]
        if table_name != "sqlite_sequence":
            print(f"table_name: {table_name}")
            row = cursor.execute(f"SELECT * FROM {table_name}")
            all_info = row.fetchall()
            for i in all_info:
                if table_name == "accounts":
                    #print(i)
                    print(f"ID: {i[0]} ||| Username: {i[1]} ||| Password: {i[2]} ||| Balance: {i[3]} ||| Address: {i[4]} |||\n"
                           f"Created_Date: {i[5]} ||| First name: {i[6]} ||| Last name: {i[7]} ||| City/Town: {i[8]} ||| States/Territories: {i[9]} |||\n"
                           f"Email: {i[10]} ||| Date of Birth: {i[11]} ||| Gender: {i[12]}")
                else: 
                    print(f"Date: {i[0]} ||| Amount: {i[1]} ||| Sender: {i[2]} ||| Reciever: {i[3]}")


if __name__ == '__main__':

    #connection = sqlite3.connect(r"C:\Users\Vangu\OneDrive\Desktop\VSCode(Python)\WebSite\data\info.db")
    #cursor = connection.cursor()
    #print_all_data()
    #print(get_data(1))
    app.run(debug=True)
    
    
    
    
    
