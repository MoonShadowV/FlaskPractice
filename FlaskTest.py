import os
from flask import Flask,request,session,g,redirect,url_for,abort,\
    render_template,flash
import mysql.connector
import pandas as pd

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

def get_id(usename):
    db = get_db()
    sql = "SELECT user_id FROM bilibili.userinfo where user_name = %s;"
    cur = db.cursor()
    cur.execute(sql,(usename,))
    user_id =cur.fetchone()
    return user_id

@app.teardown_appcontext
def close_db(erro):
    if hasattr(g,'mysql_db'):
        g.mysql_db.close()
#teardown_appcontext() 标记的函数会在每次应用环境销毁时调用。

@app.route('/show')
def show_entries():
    if 'logged_in' in session:
        id = get_id(session['username'])
        db = get_db()
        sql = "select videotag,weight from userprf where userprf.user_id = %s ORDER BY weight DESC ;"
        cur = db.cursor()
        cur.execute(sql, (id[0],))
        data = cur.fetchall()
        return render_template('UserPage.html', username=session['username'], pref=data)
    else:
        return render_template('index.html')


@app.route('/register',methods=['POST'])
def register():
#    if not session.get('logged_in'):
#       abort(401)
    u = request.form['user_name']
    db = get_db()
    cur = db.cursor()
    cur.execute('select user_name,user_password from userinfo where user_name = %s', (u,))
    content = cur.fetchone()
    if content:
        flash('用户名已存在！')
    else:
        db = get_db()
        sql = "insert into userinfo (user_name,user_password) values (%s,%s)"
        cur = db.cursor()
        cur.execute(sql,[request.form['user_name'],request.form['user_password']])
        db.commit()
        flash('注册成功！')
    return render_template('index.html')


@app.route('/',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        error = None
        if request.method == 'POST':
            session['username'] = request.form['username']
            p = request.form['password']
            db =get_db()
            cur = db.cursor()
            cur.execute('select user_name,user_password from userinfo where user_name = %s', (session['username'],))
            content = cur.fetchone()
            if content:
                username = content[0]
                password = content[1]
                if session['username'] != username:
                    #error = '用户名或密码错误'
                    flash('用户名或密码错误')
                elif p != password:
                    #error = '用户名或密码错误'
                    flash('用户名或密码错误')
                else:
                    session['logged_in'] = True
                    flash('登录成功')
                    return redirect(url_for('show_entries'))
            else:
                error = '用户名或密码错误'
    return render_template('index.html',error=error)


@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('logged_in',None)
    flash('已注销登录')
    #return redirect(url_for('show_entries'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
