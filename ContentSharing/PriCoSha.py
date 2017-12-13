#Import Flask Library
from flask import Flask, render_template, request, flash, session, url_for, redirect

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
        query = 'SELECT timest, id, content_name, file_path, likes FROM Content WHERE username = %s ORDER BY timest DESC'
        cursor.execute(query, (username))
        data = cursor.fetchall()
        query = 'SELECT id, content_name, timest, username, likes FROM Content WHERE (username != %s) AND (public = %s or id in (SELECT id FROM SHARE, Member WHERE Share.group_name = Member.group_name && Member.username = %s))'
        cursor.execute(query, (username,1, username))
        shareddata = cursor.fetchall()
        query = 'SELECT Tag.id, Content.content_name, Tag.username_tagger FROM Content JOIN Tag WHERE Tag.id = Content.id AND status= %s AND username_taggee = %s'
        cursor.execute(query, (0,username))
        pendingdata = cursor.fetchall()
        query = 'SELECT DISTINCT Member.group_name, description, Member.username from Member JOIN FriendGroup WHERE FriendGroup.group_name = Member.group_name AND Member.username_creator = FriendGroup.username AND Member.username = %s'
        cursor.execute(query, (username))
        friendgroups = cursor.fetchall()
        query = 'SELECT DISTINCT group_name, description FROM FriendGroup where username = %s'
        cursor.execute(query, (username))
        mygroups = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=username, posts=data, shared = shareddata, pending = pendingdata, friendgroups = friendgroups, mygroups = mygroups)

@app.route('/postdata', methods = ['GET', 'POST'])
def postdata():
    username = session['username']
    cursor = conn.cursor();
    content_id = request.form['content_id']
    content_name = request.form['content_name']
    content_time = request.form['content_time']
    content_user = username
    query = 'SELECT DISTINCT Comment.username, comment_text, Comment.timest FROM Comment JOIN Content WHERE Comment.id= %s'
    cursor.execute(query, (content_id))
    comments = cursor.fetchall()
    query = 'SELECT DISTINCT FriendGroup.group_name, description FROM FriendGroup JOIN Share  Where Share.ID = %s'
    cursor.execute(query, (content_id))
    groups = cursor.fetchall()
    query = 'SELECT DISTINCT username_tagger, username_taggee, Tag.timest FROM Tag JOIN Content WHERE status=1 && Tag.id = %s'
    cursor.execute(query, (content_id))
    tags = cursor.fetchall()
    cursor.close()
    return render_template('postdata.html', post_name = content_name, post_user = content_user, post_time = content_time, comments = comments, groups = groups, tags = tags)

@app.route('/groupview', methods = ['GET', 'POST'])
def groupview():
    username = session['username']
    cursor = conn.cursor();
    group_name = request.form['group_name']
    description = request.form['description']
    query = 'SELECT DISTINCT Member.username, first_name, last_name FROM Member JOIN Person WHERE Person.username = Member.username AND group_name = %s AND username_creator = %s'
    cursor.execute(query, (group_name, username))
    people = cursor.fetchall()
    cursor.close()
    return render_template('groupview.html', Friend_Group = group_name, people = people, description = description)

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

    query = 'SELECT username FROM Person WHERE username = %s'
    cursor.execute(query, (friend))
    data = cursor.fetchone()
    if not (data):
        flash('This friend does not exist')
        return redirect(url_for('home'))
    query = 'SELECT group_name FROM FriendGroup WHERE group_name = %s'
    cursor.execute(query, (group_name))
    data = cursor.fetchone()
    if not (data):
        flash('This group does not exist')
        return redirect(url_for('home'))
    query = 'SELECT username FROM FriendGroup WHERE group_name = %s AND username = %s'
    cursor.execute(query, (group_name, username))
    data = cursor.fetchone()
    if (data):
        flash('You own this friend Group')
        return redirect(url_for('home'))
    query = 'SELECT username FROM Member WHERE group_name = %s AND username = %s'
    cursor.execute(query, (group_name, username))
    data = cursor.fetchone()
    if (data):
        flash('This friend is already in this group')
        return redirect(url_for('home'))
    query = 'INSERT into Member(username, group_name, username_creator) VALUES (%s, %s, %s)'
    cursor.execute(query, (friend, group_name, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/tagFriend', methods=['GET', 'POST'])
def tagFriend():
    username_tagger = session['username']
    cursor = conn.cursor();
    content_id = request.form['content_id']
    username_taggee = request.form['username']
    query = 'SELECT id FROM Content WHERE id = %s'
    cursor.execute(query, (content_id))
    data = cursor.fetchone()
    if not (data):
        flash('This item doesnt exist')
        return redirect(url_for('home'))
    query = 'SELECT username FROM Person WHERE username = %s'
    cursor.execute(query, (username_taggee))
    data = cursor.fetchone()
    if not (data):
        flash('This person doesnt exist')
        return redirect(url_for('home'))
    query ='SELECT username FROM Content WHERE id = %s'
    cursor.execute(query, (content_id))
    data = cursor.fetchone()
    if not (username_tagger == data):
        query ='SELECT member.username FROM Share Natural Join Member where id = %s AND member.username = %s'
        cursor.execute(query, (content_id, username_tagger))
        data = cursor.fetchone()
        if not(data):
            flash('You Dont Have Access to this Item')
            return redirect(url_for('home'))
    cursor.execute(query, (content_id, username_taggee))
    data = cursor.fetchone()
    if not(data):
        flash('The person you have tagged does not have access to this item')
        return redirect(url_for('home'))
    status  = 0
    if(username_tagger == username_taggee):
        status = 1
    query = 'INSERT into Tag(id, username_taggee, username_tagger, status) VALUES (%s, %s, %s, %s)'
    cursor.execute(query, (content_id, username_taggee, username_tagger, status))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/changedescrip', methods=['GET', 'POST'])
def changedescrip():
    username = session['username']
    cursor = conn.cursor();
    newtext = request.form['edit']
    group_name = request.form['group_name']
    query = 'UPDATE FriendGroup SET description = %s WHERE group_name = %s AND username = %s'
    cursor.execute(query, (newtext, group_name, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/shareToGroup', methods=['Get', 'Post'])
def shareToGroup():
    username = session['username']
    cursor = conn.cursor();
    content_id = request.form['content_id']
    group_name = request.form['group_name']
    query = 'INSERT into Share(id, group_name, username) VALUES (%s, %s, %s)'
    cursor.execute(query,(content_id, group_name, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/likePost', methods = ['GET', 'POST'])
def likePost():
    username = session['username']
    cursor = conn.cursor();
    content_id = request.form['content_id']
    query = 'UPDATE Content SET likes = likes + 1 WHERE id = %s'
    cursor.execute(query, (content_id))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/acceptTag', methods=['GET', 'POST'])
def acceptTag():
    username = session['username']
    cursor = conn.cursor();
    posts_id = request.form['post_id']
    usernames_tagger = request.form['username_tagger']
    query = 'UPDATE Tag SET status = 1 WHERE id = %s AND username_tagger = %s AND username_taggee = %s'
    cursor.execute(query,(posts_id, usernames_tagger, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/declineTag', methods =['GET', 'POST'])
def declineTag():
    username = session['username']
    cursor = conn.cursor();
    posts_id = request.form['post_id']
    usernames_tagger = request.form['username_tagger']
    query = 'DELETE from Tag WHERE id = %s AND username_tagger = %s AND username_taggee = %s'
    cursor.execute(query,(posts_id, usernames_tagger, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/addComment', methods = ['GET','POST'])
def addComment():
    username = session['username']
    cursor = conn.cursor();
    comment = request.form['comment']
    content_id = request.form['content_id']
    query = 'INSERT into Comment(id, comment_text, username) VALUES(%s,%s,%s)'
    cursor.execute(query,(content_id, comment, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/leaveGroup', methods=['GET', 'POST'])
def leaveGroup():
    username = session['username']
    cursor = conn.cursor();
    group_name = request.form['group_name']
    owner = request.form['username']
    query = 'DELETE from Comment where comment.username, comment.id in (SELECT DISTINCT comment.username, comment.id from Comment JOIN Content JOIN Share where comment.id = content.id AND content.id = share.id AND share.group_name = %s AND share.username = %s)'
    cursor.execute(query, (group_name, owner))
    query = 'DELETE from Member where username = %s AND group_name = %s AND username_creator = %s'
    cursor.execute(query,(username, group_name, owner))
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
