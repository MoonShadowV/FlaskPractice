import os
import sqlite3
from flask import Flask,request,session,g,redirect,url_for,abort,\
    render_template,flash

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE = os.path.join(app.root_path,'flasktest.db'),
    SECRET_KEY = 'key',
    USERNAME = 'admin',
    PASSWORD = '+1s'
))
app.config.from_envvar('FLASKETEST_SETTINGS',silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(erro):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('SELECT title,content FROM entries ORDER BY id DESC ')
    entries = cur.fetchall()
    return render_template('show_entries.html',entries=entries)


@app.route('/add',methods=['POST'])
def add_entry():
    if not session.get('logged in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, content) values (?, ?)',
                 [request.form['title'], request.form['content']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        error = None
        if request.method == 'POST':
            if  request.form['username'] != app.config['USERNAME']:
                error = 'Invalid username'
            elif request.form['password'] != app.config['PASSWORD']:
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
