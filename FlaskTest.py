import os
from flask import Flask,request,session,g,redirect,url_for,abort,\
    render_template,flash
import mysql.connector

app = Flask(__name__)
app.config.from_object(__name__)


app.config.update(dict(
    SECRET_KEY = 'key',
))
app.config.from_envvar('FLASKETEST_SETTINGS',silent=True)

def connect_db():
    conn = mysql.connector.connect(user='root',password='8749654',database='bilibili')
    return conn

"""
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
"""

def get_db():
    if not hasattr(g,'mysql_db'):
        g.mysql_db = connect_db()
    return g.mysql_db


@app.teardown_appcontext
def close_db(erro):
    if hasattr(g,'mysql_db'):
        g.mysql_db.close()

@app.route('/')
def show_entries():
    db = get_db()
    ##cur = db.execute('SELECT title,content FROM entries ORDER BY id DESC ')
    sql = "select user_name,videotag,weight " \
          "from userinfo,userprf " \
          "where userinfo.user_id = userprf.user_id;"
    cur = db.cursor()
    cur.execute(sql)
    entries = cur.fetchall()
    return render_template('show_entries.html',entries=entries)


@app.route('/register',methods=['POST'])
def register():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    ##db.execute('insert into entries (title, content) values (?, ?)',
    ##             [request.form['title'], request.form['content']])
    sql = "insert into userinfo (user_name,user_password) values (%s,%s)"
    cur = db.cursor()
    cur.execute(sql,[request.form['user_name'],request.form['user_password']])
    db.commit()
    flash('New user was successfully registed!')
    return redirect(url_for('show_entries'))


@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        error = None
        if request.method == 'POST':
            if  request.form['username'] != 'admin':
                error = 'Invalid username'
            elif request.form['password'] != 'default':
                error = 'Invalid password'
            else:
                session['logged_in'] = True
                flash('You were logged in')
                return redirect(url_for('show_entries'))
    return render_template('login.html',error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in',None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()
