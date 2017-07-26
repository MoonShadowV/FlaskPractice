import os
from flask import Flask,request,session,g,redirect,url_for,abort,\
    render_template,flash
import mysql.connector
import pandas as pd
import multiprocessing,math

app = Flask(__name__)
app.config.from_object(__name__)
echo = 'Echo'

app.config.update(dict(
    SECRET_KEY = 'This is a secret key, which is a secret.',
))
app.config.from_envvar('FLASKETEST_SETTINGS',silent=True)

ProLock = multiprocessing.Lock()#进程IO互斥锁

#预先把视频数据存储到服务器内存中
db = mysql.connector.connect(user='root',password='8749654',database='bilibili')

videoData = pd.read_sql("SELECT * FROM bilibili.bilibilidata;", db)
videoData.ix[:,8:] = videoData.ix[:,8:].replace('',pd.np.nan)#把空字符串替换为nan方便内建函数处理

Sim = pd.Series()

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
#teardown_appcontext() 标记的函数会在每次应用环境销毁时调用。

def get_id(usename):
    db = get_db()
    sql = "SELECT user_id FROM bilibili.userinfo where user_name = %s;"
    cur = db.cursor()
    cur.execute(sql,(usename,))
    user_id =cur.fetchone()
    return user_id




def Algorithm(videoData,userData):#算法主体部分
    # videoData 视频数据,DataFrame类型
    # userData 用户偏好表,Series类型

    videoIndex = videoData.ix[:,2:8]#视频热度数据
    videoAid = videoData["aid"]#视频的Aid
    videoTag = videoData.ix[:,8:]#视频标签
    videoNum = videoData.__len__()#视频数量


    similarity = {}#余弦相似度度量，字典类型，key为视频aid

    userPrefVictor = mod(userData)#用户偏好向量的模值.


    for i in range(100000,105000):
        videoVictor = pd.Series(data=1,index=videoTag.iloc[i].dropna().values)#构造视频向量
        videoValue = len(videoTag.iloc[i].dropna())
        dot = (videoVictor * userData).dropna().sum()#计算内积
        print(i)
        if dot > 0.5:
            similarity[videoAid.iloc[i]] = dot / (videoValue+userPrefVictor)#余弦相似度

    global Sim
    Sim = pd.Series(similarity)
    Sim = Sim.sort_values(0,0)

    """
    #互斥，以便进行IO操作
    ProLock.acquire()
    if not hasattr(g, 'sim'):
        print('Arfa')
        g.sim = pd.Series()
    else:
        print('Finda')
        g.sim = g.sim.append(similarity)
    ProLock.release()
    """


#取模运算
def mod(data):
    sum = 0
    length = len(data)
    for i in range(length):
        sum  += data[i]**2
    return math.sqrt(sum)

"""
def runAlgorithm(Data,userData):
    #对数据分片，以便多进程
    data1 = Data[:100000]
    data2 = Data[100000:200000]
    data3 = Data[200000:300000]
    data4 = Data[300000:400000]
    data5 = Data[400000:]
    #多进程
    C1 = multiprocessing.Process(target=Algorithm,args=(data1,userData))
    C1.start()

    C2 = multiprocessing.Process(target=Algorithm, args=(data2, userData))
    C2.start()

    C3 = multiprocessing.Process(target=Algorithm, args=(data3, userData))
    C3.start()

    C4 = multiprocessing.Process(target=Algorithm, args=(data4, userData))
    C4.start()

    C5 = multiprocessing.Process(target=Algorithm, args=(data5, userData))
    C5.start()
    C5.join()
"""

@app.route('/updateUserPref/')
def updateUserPref():
    user_id = session['id']
    aid = request.args.get('aid')
    print(aid)
    db = get_db()
    cur = db.cursor()

    #获取视频标签
    cur.execute("SELECT * FROM bilibili.bilibilidata where aid = %s;",(aid,))
    tag = cur.fetchone()
    tag = pd.Series(tag)[8:]

    userPref = session['userpref']
    print(userPref)

    for i in tag:
        if i:
            if i in userPref:
                weight = userPref[i]+1
                sql = "UPDATE `bilibili`.`userprf` SET `weight`=%s WHERE  `user_id`= %s and videotag = %s;"
                cur.execute(sql,(weight,user_id,i,))
                db.commit()
            else:
                print(i)
                sql = ("INSERT INTO `bilibili`.`userprf` (`user_id`, `videotag`, `weight`) VALUES (%s, %s, %s);")
                cur.execute(sql, (user_id, i,1,))
                db.commit()

    return aid



@app.route('/recommand/')
def recommand():
    if 'logged_in' in session:
        id = get_id(session['username'])
        session['id'] = id[0]
        db = get_db()
        sql = "select videotag,weight from userprf where userprf.user_id = %s ORDER BY weight DESC ;"
        cur = db.cursor()
        cur.execute(sql, (id[0],))
        userData = cur.fetchall()
        userData = pd.Series(dict(userData))

        with app.app_context():
            Algorithm(videoData,userData)

        print('Beta')

        strtemp = "https://www.bilibili.com/video/av"
        data = []
        if not hasattr(g,'sim'):
            print('Echo')
            g.sim = Sim
            g.sim.sort_values(0,0)
            for i in g.sim.head(20).items():
                aid = i[0]
                url = strtemp+str(aid)
                title = videoData[videoData['aid'] == aid].iloc[0][0]
                intro = videoData[videoData['aid'] == aid].iloc[0][1]
                weight = round(i[1],5)
                data.append([title,url,aid,intro,weight])
        return render_template('RecommandPage.html',username=session['username'],data=data)

@app.route('/show/')
def show_entries():
    if 'logged_in' in session:
        id = get_id(session['username'])
        db = get_db()
        sql = "select videotag,weight from userprf where userprf.user_id = %s ORDER BY weight DESC ;"
        cur = db.cursor()
        cur.execute(sql, (id[0],))
        data = cur.fetchall()
        session['userpref'] = dict(data)
        return render_template('UserPage.html', username=session['username'], pref=data)
    else:
        return render_template('index.html')


@app.route('/register/',methods=['POST'])
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


@app.route('/logout/')
def logout():
    session.pop('username',None)
    session.pop('logged_in',None)
    flash('已注销登录')
    #return redirect(url_for('show_entries'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run()

