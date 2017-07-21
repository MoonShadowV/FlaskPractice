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


@app.teardown_appcontext
def close_db(erro):
    if hasattr(g,'mysql_db'):
        g.mysql_db.close()

@app.route('/show')
def show_entries():
    db = get_db()
    sql = "select videotag,weight " \
          "from userinfo,userprf " \
          "where userinfo.user_name = %s ORDER BY weight DESC ;"
    cur = db.cursor()
    cur.execute(sql,(session['username'],))
    data = cur.fetchall()
    """
    preference = pd.DataFrame(d,columns=['username','tag','weight']).ix[:,1:]
    data = {}
    for i in range(preference.shape[0]):
        data[preference.ix[i][0]] = preference.ix[i][1]
    """
    return render_template('UserPage.html',username=session['username'],pref = data)


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
