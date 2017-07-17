import os
from flask import Flask,request,session,g,redirect,url_for,abort,\
    render_template,flash
import mysql.connector

app = Flask(__name__)
app.config.from_object(__name__)


app.config.update(dict(
    SECRET_KEY = 'This is a secret key, which is a secret.',
))
app.config.from_envvar('FLASKETEST_SETTINGS',silent=True)

def connect_db():
    conn = mysql.connector.connect(user='root',password='8749654',database='bilibili')
    return conn

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
    sql = "insert into userinfo (user_name,user_password) values (%s,%s)"
    cur = db.cursor()
    cur.execute(sql,[request.form['user_name'],request.form['user_password']])
    db.commit()
    flash('注册成功！')
    return redirect(url_for('show_entries'))


@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        error = None
        if request.method == 'POST':
            u = request.form['username']
            p = request.form['password']
            db =get_db()
            cur = db.cursor()
            cur.execute('select user_name,user_password from userinfo where user_name = %s', (u,))
            content = cur.fetchone()
            username = content[0]
            password = content[1]
            if  u != username:
                error = '用户名或密码错误'
            elif p != password:
                error = '用户名或密码错误'
            else:
                session['logged_in'] = True
                flash('登录成功')
                return redirect(url_for('show_entries'))
    return render_template('login.html',error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in',None)
    flash('已注销登录')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()
