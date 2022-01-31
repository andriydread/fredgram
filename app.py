from shutil import unregister_unpack_format
from flask import Flask, render_template, request, redirect
import os
import psycopg2
import bcrypt
import secrets

app = Flask(__name__)



# Func to validate if user is logged

def validate_user():
    user_id = postgres_sessions('check_token', token=request.cookies.get('session'))
    if user_id != None:
        return user_id[0]
    return None


# Sorts and does stuff to list of messages

def do_stuff_with_messages(list_of_messages):
    list_of_edited_messages = []
    for message in list_of_messages:
        lis_message = list(message)
        lis_message[1] = postgres_profiles('what_user', id=lis_message[1])[0]
        lis_message[2] = postgres_profiles('what_user', id=lis_message[2])[0]
        list_of_edited_messages.append(lis_message)
    list_of_sorted_messages = sorted(list_of_edited_messages, key=lambda x: x[0], reverse=True)
    return list_of_sorted_messages




# Func to connect to PROFILES table

def postgres_profiles(method, login=None, password=None, id=None):
    psql = psycopg2.connect(host=os.environ['POST_HOST'], user=os.environ['POST_USER'], password=os.environ['POST_PASSWORD'], database=os.environ['POST_DB'])
    try: 
        psql.autocommit = True
        cursor = psql.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS profiles(id SERIAL PRIMARY KEY, login varchar(200), pass bytea, salt bytea, UNIQUE(login));"""
        )

        if method == 'register_user':
            password = str.encode(password)
            salt = bcrypt.gensalt()
            hashed_pass = bcrypt.hashpw(password, salt)
            cursor.execute(
                """INSERT INTO profiles (login, pass, salt) VALUES (%s, %s, %s);""", (login, hashed_pass, salt,)
            )

        elif method == 'login_user':
            cursor.execute(
                """SELECT id, pass, salt FROM profiles WHERE login=%s;""", (login,)
            )

            return cursor.fetchone()

        elif method == 'get_user_id':
            cursor.execute(
                """SELECT id FROM profiles WHERE login=%s;""", (login, )
            )

            return cursor.fetchone()

        elif method == 'find_all_users':
            cursor.execute(
                """SELECT id, login FROM profiles;"""
            )

            return cursor.fetchall()

        elif method == 'what_user':
            cursor.execute(
                """SELECT login FROM profiles WHERE id=%s;""", (id,)
            )

            return cursor.fetchone()


    except Exception as ex:
        print('Error occured', ex)
    
    finally:
        if psql:
            cursor.close()
            psql.close()




# Func to connect to SESSIONS table

def postgres_sessions(method, id=None, token=None):
    psql = psycopg2.connect(host=os.environ['POST_HOST'], user=os.environ['POST_USER'], password=os.environ['POST_PASSWORD'], database=os.environ['POST_DB'])
    try: 
        psql.autocommit = True
        cursor = psql.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS sessions(id SERIAL PRIMARY KEY, user_id BIGINT, token varchar(50));"""
        )

        if method == 'create_token':
            cursor.execute(
                """INSERT INTO sessions(user_id, token) VALUES (%s, %s);""", (id, token, )
            )

        elif method == 'check_token':
            cursor.execute(
                """SELECT user_id FROM sessions WHERE token=%s;""", (token, )
            )

            return cursor.fetchone()
        

    except Exception as ex:
        print('Error occured', ex)
    
    finally:
        if psql:
            cursor.close()
            psql.close()




# Func to connect to messages table

def postgres_messages(method, user_id_to=None, user_id_from=None, text=None, token=None):
    psql = psycopg2.connect(host=os.environ['POST_HOST'], user=os.environ['POST_USER'], password=os.environ['POST_PASSWORD'], database=os.environ['POST_DB'])
    try: 
        psql.autocommit = True
        cursor = psql.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS message(id SERIAL PRIMARY KEY, user_id_from BIGINT NOT NULL, user_id_to BIGINT NOT NULL, text TEXT, token varchar(50));"""
        )


        if method == 'send_text':
            cursor.execute(
                """INSERT INTO message(user_id_from, user_id_to, text, token) VALUES(%s, %s, %s, %s);""", (user_id_from, user_id_to, text, token)
            )

        elif method == 'get_received_messages':
            cursor.execute(
                """SELECT * FROM message WHERE user_id_to=%s;""", (user_id_to,)
            )
            return cursor.fetchall()

        elif method == 'get_sent_messages':
            cursor.execute(
                """SELECT * FROM message WHERE user_id_from=%s;""", (user_id_from,)
            )
            return cursor.fetchall()

        elif method == 'get_messages_by_token':
            cursor.execute(
                """SELECT * FROM message WHERE token=%s;""", (token,)
            )
            return cursor.fetchall()

    
    except Exception as ex:
        print('Error occured', ex)
    
    finally:
        if psql:
            cursor.close()
            psql.close()




# Func to connect to tokens for messages table

def postgres_chats_tokens(method, user_id_1=None, user_id_2=None):
    psql = psycopg2.connect(host=os.environ['POST_HOST'], user=os.environ['POST_USER'], password=os.environ['POST_PASSWORD'], database=os.environ['POST_DB'])
    try:
        psql.autocommit = True
        cursor = psql.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS chat_tokens(id SERIAL PRIMARY KEY, user_id_1 BIGINT NOT NULL, user_id_2 BIGINT NOT NULL, token varchar(50));"""
        )

        user_1 = user_id_1
        user_2 = user_id_2

        if user_id_2 < user_id_1:
            user_1 = user_id_2
            user_2 = user_id_1
        else:
            pass

        if method == 'create_chat_token':
            cursor.execute(
                """SELECT * from chat_tokens WHERE user_id_1=%s AND user_id_2=%s;""", (user_1, user_2, )
            )
            result = cursor.fetchone()
            if result == None:
                cursor.execute(
                    """INSERT INTO chat_tokens(user_id_1, user_id_2, token) VALUES(%s, %s, %s);""", (user_1, user_2, secrets.token_hex(10))
                )
            else:
                return True


        if method == 'get_token':
            cursor.execute(
                """SELECT token from chat_tokens WHERE user_id_1=%s AND user_id_2=%s;""", (user_1, user_2, )
            )
            return cursor.fetchone()




    except Exception as ex:
        print('Error occured', ex)
    
    finally:
        if psql:
            cursor.close()
            psql.close()            





# Route to display register html

@app.route('/register.html')
def register_html():
    return render_template('register.html')

# Saves user to db

@app.route('/register_user', methods=['POST'])
def register():
    postgres_profiles('register_user', login=request.form['login'], password=request.form['password'])
    return render_template('login.html')




# Route to display login

@app.route('/login.html')
def login_html():
    return render_template('login.html')

# Create cookie for registered user

@app.route('/login_user', methods=['POST'])
def login():

    login = request.form['login']
    data = postgres_profiles('login_user', login=login)
    
    if data != None:
        salt = data[2].tobytes()
        bytes_password = str.encode(request.form['password'])
        hashed_pass = bcrypt.hashpw(bytes_password, salt)

        if data[1].tobytes() == hashed_pass:
            token = secrets.token_hex(10)
            postgres_sessions('create_token', id = data[0], token=token)
            res = redirect('/')
            res.set_cookie('session', token)
            return res
        return redirect('login.html')

    return redirect('login.html')





# Routes to show all users

@app.route('/')
def index():
    if validate_user() != None:

        return render_template('index.html', users=postgres_profiles('find_all_users'), user=postgres_profiles('what_user', id=validate_user()))

    return redirect('login.html')





# # Route to send and view messages

# @app.route('/text.html')
# def view():
#     if validate_user() != None:

#         sent_messages = postgres_messages('get_sent_messages', user_id_from=validate_user())
#         received_messages = postgres_messages('get_received_messages', user_id_to=validate_user())
#         all_messages = sent_messages + received_messages
#         return render_template('text.html', user=postgres_profiles('what_user', id=validate_user()), messages=do_stuff_with_messages(all_messages))

#     return redirect('/login.html')


# @app.route('/send_text', methods=['POST'])
# def text_send():
#     if validate_user() != None:

#         to_whom_id = postgres_profiles('get_user_id', request.form['to'])
#         postgres_messages('send_text', user_id_from=validate_user(), user_id_to=to_whom_id, text=request.form['text'])
#         return redirect('/text.html')

#     return redirect('/login.html')




# Route to pick user to start chating

@app.route('/pick_user', methods=['POST'])
def pick_user():
    if validate_user() != None:

        user_to_id = int(request.form['user_to_id'])
        user_from_id = validate_user()

        postgres_chats_tokens('create_chat_token', user_id_1=user_from_id, user_id_2=user_to_id)
        token = postgres_chats_tokens('get_token', user_id_1=user_from_id, user_id_2=user_to_id)

        all_messages = postgres_messages('get_messages_by_token', token=token[0])
 
        return render_template('message.html', user=postgres_profiles('what_user', id=user_from_id), user_to=postgres_profiles('what_user', id=user_to_id), messages=do_stuff_with_messages(all_messages))

    return redirect('/login.html')



@app.route('/send_message', methods=['POST'])
def send_message():
    if validate_user() != None:

        user_from_id = validate_user()
        user_to_id = postgres_profiles('get_user_id', request.form['to'])

        token = postgres_chats_tokens('get_token', user_id_1=user_from_id, user_id_2=user_to_id[0])

        postgres_messages('send_text', token=token, user_id_to=user_to_id[0], user_id_from=validate_user(), text=request.form['text'])

        all_messages = postgres_messages('get_messages_by_token', token=token[0])

        return render_template('message.html', user=postgres_profiles('what_user', id=user_from_id), user_to=postgres_profiles('what_user', id=user_to_id), messages=do_stuff_with_messages(all_messages))

    return redirect('/login.html')



if __name__ == '__main__':
    app.run(debug=True)
