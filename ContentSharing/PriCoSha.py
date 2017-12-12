#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import datetime
import time

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                           port = 8889,
                           user='root',
                           password='root',
                           db='PriCoSha',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
        return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
        return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
        return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
        #grabs information from the forms
        username = request.form['username']
        password = request.form['password']
        #cursor used to send queries
        cursor = conn.cursor()
        #executes query
        query = 'SELECT * FROM Person WHERE username = %s and password = %s'
        h = hashlib.md5(password.encode())
        cursor.execute(query, (username, h.hexdigest()))
        #stores the results in a variable
        data = cursor.fetchone()
        #use fetchall() if you are expecting more than 1 data row
        cursor.close()
        error = None
        if(data):
                #creates a session for the the user
                #session is a built in
                session['username'] = username
                return redirect(url_for('home'))
        else:
                #returns an error message to the html page
                error = 'Invalid login or username'
                return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])

def registerAuth():
        #grabs information from the forms
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        h = hashlib.md5(password.encode())

        #cursor used to send queries
        cursor = conn.cursor()
        #executes query
        query = 'SELECT * FROM Person WHERE username = %s'
        cursor.execute(query, (username))
        #stores the results in a variable
        data = cursor.fetchone()
        #use fetchall() if you are expecting more than 1 data row
        error = None
        if(data):
                #If the previous query returns data, then user exists
                error = "This user already exists"
                return render_template('register.html', error = error)
        else:
                ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s)'
                cursor.execute(ins, (username, h.hexdigest(), first_name, last_name))
                conn.commit()
                cursor.close()
                return render_template('index.html')

@app.route('/home')
def home():
        username = session['username']
        cursor = conn.cursor();
        query = 'SELECT timest, id FROM Content WHERE username = %s ORDER BY timest DESC'
        cursor.execute(query, (username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=username, posts=data)

@app.route('/post', methods=['GET', 'POST'])
def post():
        username = session['username']
        cursor = conn.cursor();
        content_name = request.form['content_name']
        file_path = request.form['file_path']
        public = 0
        if request.form.get('public'):
                public = 1
        query = 'INSERT INTO Content ( username, file_path, content_name, public) VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (username, file_path, content_name, public))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/makeFriendGroup', methods=['GET', 'POST'])
def makeFriendGroup():
    username = session['username']
    cursor = conn.cursor();
    group_name = request.form['group_name']
    description = request.form['description']
    friendOne = request.form['username1']
    friendTwo = request.form['username2']
    query = 'INSERT into FriendGroup (username, group_name, description) VALUES (%s, %s, %s)'
    cursor.execute(query, (username, group_name, description))
    query = 'INSERT into Member(username, group_name, username_creator) VALUES (%s, %s, %s)'
    cursor.execute(query, (friendOne, group_name, username))
    cursor.execute(query, (friendTwo, group_name, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/addFriend', methods=['GET', 'POST'])
def addFriend():
    username = session['username']
    cursor = conn.cursor();
    group_name = request.form['group_name']
    friend = request.form['username']
    query = 'INSERT into Member(username, group_name, username_creator) VALUES (%s, %s, %s)'
    cursor.execute(query, (friend, group_name, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))



@app.route('/logout')
def logout():
        session.pop('username')
        return redirect('/')

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
        app.run('127.0.0.1', 5000, debug = True)
