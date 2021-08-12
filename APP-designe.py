from flask import Flask, render_template, request, json, jsonify, Response, redirect, session
from flask_login import login_required
from flask_sqlalchemy import SQLAlchemy
import smtplib
import pymysql
import cv2
import numpy as np
import os
import json
from datetime import datetime
import datetime as DT
from models.user import User
from werkzeug.security import generate_password_hash
import uuid
from flask_login import login_user, login_required
from flask_login import LoginManager, current_user
from flask_login import logout_user
import time
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'app-design',
        'charset': 'utf8',
        'cursorclass': pymysql.cursors.Cursor,
    }
app.secret_key = os.urandom(24)
# use login manager to manage session
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app=app)
def sql_fetch_json(cursor: pymysql.cursors.Cursor):

    keys = []
    for column in cursor.description:
        keys.append(column[0])
    key_number = len(keys)

    json_data = []
    for row in cursor.fetchall():
        item = dict()
        for q in range(key_number):
            item[keys[q]] = row[q]
        json_data.append(item)

    return json_data
@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/graphics')
def graphics():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from graphics "
    count = cursor.execute(sql)
    count = { "count": count}
    results = getGraphicsTreeData()
    db.commit()
    db.close()
    return render_template("graphics/graphics.html", count= count, graphicsFenleis = results, username= session.get("username"))
@app.route('/graphicsFenlei')
def graphicsFenlei():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from graphicsFenlei"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    # result = json.dumps(treeData,ensure_ascii=False)
    return render_template("graphics/graphicsFenlei.html", treeData= treeData)
@app.route('/graphicsList', methods=['POST', 'GET'])
def graphicsList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    keyValues = request.args.get("keyValues")
    print(keyValues)
    if keyValues!=None and keyValues!="" :
        keyValues=tuple(str(keyValues).split(","))
    else:
        keyValues = []
    query = request.args.get("q")
    start = (page-1)*size
    print(start, size)
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    sql = "select * from graphics WHERE  status = 1"
    if query !=None and query !="":
        if len(keyValues) == 0:
            sql="select * from graphics WHERE type like '{}' or provider like '{}' and status = 1".format(query, query)
        else:
            sql = "select * from graphics WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
    if len(keyValues)>0:
        if query != None and query != "":
            sql= "select * from graphics WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
        else:
            sql= "select * from graphics WHERE type in {} and status = 1".format(keyValues)

    sql1 = sql +" order by creatDate desc" +" limit {}, {}".format(start, size)
    sql2 = sql +" order by creatDate desc"
    print(sql1)
    print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)

    glist = sql_fetch_json(cursor1)
    results = {"data":glist, "count":count}
    db.commit()
    db.close()
    return render_template("graphics/graphicsList.html", graphicslist= results)

@app.route('/saveGraphicFenleiRoot', methods=['POST', 'GET'])
def saveGraphicFenleiRoot():
    title = request.form.get("title")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from graphicsFenlei WHERE father = -1"
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = "fenlei-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = "fenlei-" + str(max(V) + 1)
    sql1 = "INSERT INTO  graphicsFenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, -1)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})


@app.route('/saveGraphicFenleiSecond', methods=['POST', 'GET'])
def saveGraphicFenleiSecond():
    title  = request.form.get("title")
    father = request.form.get("father")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from graphicsFenlei WHERE father = '{}'".format(father)
    print(sql)
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = father + "-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = father + "-" + str(max(V) + 1)
    sql1 = "INSERT INTO  graphicsFenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, father)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        treeData = getGraphicsTreeData()
        print(treeData)
        return jsonify({'status': '1', 'msg': '保存成功!', 'treeData':treeData})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})
@app.route('/updateGraphicsFenlei', methods=['POST', 'GET'])
def updateGraphicsFenlei():
    fenleis  = request.form.get('fenleidata')
    fenleis = json.loads(fenleis)
    db = pymysql.connect(**config)
    try:
        for f in fenleis:
            cursor = db.cursor()
            title = f["title"]
            value = f["value"]
            sql = "update graphicsFenlei set title='{}' where value ='{}'".format(title, value)
            print(sql)
            cursor.execute(sql)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '保存失败!'})
@app.route('/deleteGraphicsFenlei', methods=['POST','GET'])
def deleteGraphicsFenlei():
    delId = request.form.get('delId')
    db = pymysql.connect(**config)
    sql1 = "select father from graphicsFenlei WHERE value ='{}'".format(delId)
    sql2 = "delete from graphicsFenlei where value ='{}'".format(delId)

    print(sql1)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()
    cursor1.execute(sql1)
    result = sql_fetch_json(cursor1)
    father = result[0]['father']
    sql3 = "delete from graphicsFenlei where father ='{}'".format(delId)

    try:
        if father == '-1':
            cursor2.execute(sql2)
            cursor3.execute(sql3)
            print(sql2)
            print(sql3)
            db.commit()
        else:
            cursor2.execute(sql2)
            print(sql2)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})

def getGraphicsTreeData():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from graphicsFenlei"
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return treeData

@app.route('/login', methods=['POST','GET'])
def login():
    return render_template('login.html')

@app.route('/saveRegister', methods=['POST','GET'])
def saveRegister():
    username = request.form.get("username")
    password = request.form.get("password")
    user = User(username)
    try:
        user.password =password
        return jsonify({'status': '1', 'msg': '注册成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '注册失败，该用户已存在!'})





@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/toLogin', methods=['POST','GET'])
def toLogin():
    username = request.args.get("username")
    password = request.args.get("password")
    print(username, password)
    remember_me = request.form.get('remember_me', True)
    user = User(username)
    if user.verify_password(password):
        print("登陆成功")
        login_user(user, remember=remember_me)
        session["username"] = username
        return redirect(request.args.get('next') or '/')
    else:
        session["username"] = ""
        print("登陆失败")
        return render_template('login.html')
@app.route('/logout', methods=['POST','GET'])
@login_required
def logout():
    session["username"] =None
    next = request.args.get("next")
    if next =="" or next ==None:
        next = "/index"
    logout_user()
    return redirect(next)

@app.route('/main')
@login_required
def main():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    userId = current_user.id
    user = User(current_user.username)
    result = user.findByUserId(userId)
    menuIds = str(result['menuIds'])
    if menuIds!=None or menuIds!="":
        menuIdsArray = menuIds.split(",")
    else:
        menuIdsArray =[]
    queryArray = tuple(menuIdsArray)
    sql = "select * from mainTree where value in {}".format(queryArray)
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return render_template('main.html', treeData=treeData, username=current_user.username)

@app.route('/mainTree')
def mainTree():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from mainTree"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return render_template("mainTree.html", treeData= treeData)

@app.route('/saveMainTreeRoot', methods=['POST', 'GET'])
def saveMainTreeRoot():
    title = request.form.get("title")
    icon = request.form.get("icon")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from mainTree WHERE father = -1"
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = "main-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = "main-" + str(max(V) + 1)
    sql1 = "INSERT INTO  mainTree (value,title, father, icon )VALUES ('{}','{}','{}','{}')".format(value, title, -1, icon)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该菜单已存在!'})

@app.route('/saveMainTreeSecond', methods=['POST', 'GET'])
def saveMainTreeSecond():
    title  = request.form.get("title")
    father = request.form.get("father")
    url = request.form.get("url")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from mainTree WHERE father = '{}'".format(father)
    print(sql)
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = father + "-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = father + "-" + str(max(V) + 1)
    sql1 = "INSERT INTO  mainTree (value,title, father, url )VALUES ('{}','{}','{}','{}')".format(value, title, father,url)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该菜单已存在!'})
@app.route('/updateMainTree', methods=['POST', 'GET'])
def updateMainTree():
    nodes  = request.form.get('nodedata')
    nodes = json.loads(nodes)
    db = pymysql.connect(**config)
    try:
        for f in nodes:
            cursor = db.cursor()
            title = f["title"]
            icon =f["icon"]
            url = f["url"]
            value = f["value"]
            sql = "update mainTree set title='{}', icon='{}', url='{}' where value ='{}'".format(title,icon, url, value)
            print(sql)
            cursor.execute(sql)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '保存失败!'})
@app.route('/deleteMainTree', methods=['POST','GET'])
def deleteMainTree():
    delId = request.form.get('delId')
    db = pymysql.connect(**config)
    sql1 = "select father from mainTree WHERE value ='{}'".format(delId)
    sql2 = "delete from mainTree where value ='{}'".format(delId)

    print(sql1)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()
    cursor1.execute(sql1)
    result = sql_fetch_json(cursor1)
    father = result[0]['father']
    sql3 = "delete from graphicsFenlei where father ='{}'".format(delId)

    try:
        if father == '-1':
            cursor2.execute(sql2)
            cursor3.execute(sql3)
            print(sql2)
            print(sql3)
            db.commit()
        else:
            cursor2.execute(sql2)
            print(sql2)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})
@app.route('/userManage')
def userManage():
    return render_template("user/userManage.html")

@app.route('/userList', methods=['POST','GET'])
def userList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    user = User(current_user.username)
    result = user.userList(page,size,query)
    return result
@app.route('/getQuanXianTree',methods=['POST','GET'])
def getQuanXianTree():
    userId = request.args.get("userId")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from mainTree"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    user = User(current_user.username)
    result = user.findByUserId(userId)
    menuIds = result['menuIds']
    return render_template("user/quanXianTree.html", treeData= treeData, menuIds= menuIds, userId= userId)

@app.route('/updateQuanXian', methods=['POST', 'GET'])
def updateQuanXian():
    menuIds = request.form.get('menuIds')
    userId = request.form.get('userId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update user set menuIds='{}' where userId ='{}'".format(menuIds,userId)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '修改成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '修改失败!'})


@app.route('/sysGraphicsManage')
def sysGraphicsManage():
    return render_template("graphics/graphicsManage.html")

@app.route('/graphicsManageList', methods=['POST', 'GET'])
def graphicsManageList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from graphics order by creatDate desc limit {}, {} ".format(start, size)
        sql2 = "select * from graphics order by creatDate desc"
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from graphics where type like '{}' order by creatDate desc limit {}, {} ".format(query, start, size)
        sql2 = "select * from graphics where type like '{}' order by creatDate desc ".format(query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)


@app.route('/updateGraphicsStaus', methods=['POST', 'GET'])
def updateGraphicsStaus():
    status = request.form.get('status')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update graphics set status={} where imageId ='{}'".format(int(status),imageId)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '修改成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '修改失败!'})
@app.route('/addGraphicStorage', methods=['POST', 'GET'])
def addGraphicStorage():
    status = request.form.get('storageStatus')
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)

    sql = "select storageNum from graphics where imageId = '{}'".format(imageId)
    cursor = db.cursor()
    cursor.execute(sql)
    storageNums = sql_fetch_json(cursor)
    storageNum = int(storageNums[0]["storageNum"])

    if status =="1":
        try:
            cursor1 = db.cursor()
            sql1 = "select * from graphics where imageId = '{}'".format(imageId)
            print(sql1)
            cursor1.execute(sql1)
            graphics = sql_fetch_json(cursor1)
            graphic = graphics[0]
            storageId = username + imageId
            sql2 = "INSERT INTO  graphicsStorage (username,imageId, imageUrl, title, type, provider, creatDate,storageId ) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')".format(
                                            username, imageId,graphic['imageUrl'],
                                           graphic['title'],graphic['type'],
                                           graphic['provider'],graphic['creatDate'], storageId)
            print(sql2)
            cursor2 = db.cursor()
            cursor2.execute(sql2)

            storageNum = storageNum + 1
            sql2_ = "update  graphics set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor2_ = db.cursor()
            cursor2_.execute(sql2_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '收藏成功!'})
        except Exception:
            return jsonify({'status': '0', 'msg': '该数据已收藏!'})
    if status =="0":
        try:
            cursor3 = db.cursor()
            sql3 = "delete from graphicsStorage where imageId ='{}'".format(imageId)
            cursor3.execute(sql3)

            storageNum = storageNum - 1
            sql3_ = "update  graphics set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor3_ = db.cursor()
            cursor3_.execute(sql3_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '取消收藏!'})
        except Exception:

            return jsonify({'status': '0', 'msg': '取消收藏失败!'})

@app.route('/getMySorageGraphicsById', methods=['POST', 'GET'])
def getMySorageGraphicsById():
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "select * from graphicsStorage where username='{}' and imageId ='{}'".format(username,imageId)
        print(sql)
        count = cursor.execute(sql)
        db.commit()
        db.close()
        if count >0:
            return jsonify({'status': '1'})
        else:
            return jsonify({'status': '0'})
    except Exception:

        return jsonify({'status': '0'})

@app.route('/graphicsStorageManage')
def graphicsStorageManage():
    return render_template("graphics/graphicsStorageManage.html")
@app.route('/graphicsStorageManageList', methods=['POST', 'GET'])
def graphicsStorageManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from graphicsstorage where username = '{}' limit {}, {} ".format(username, start, size)
        sql2 = "select * from graphicsstorage where username = '{}'".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from graphicsstorage where username = '{}' and type like '{}' limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from graphicsstorage where username = '{}' and type like '{}' ".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/myGraphicsManageList', methods=['POST', 'GET'])
def myGraphicsManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from graphics where provider = '{}' order by creatDate desc limit {}, {} ".format(username, start, size)
        sql2 = "select * from graphics where provider = '{}' order by creatDate desc".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from graphics where provider = '{}' and type like '{}' order by creatDate desc limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from graphics where provider = '{}' and type like '{}' order by creatDate desc".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/myGraphicsManage')
def myGraphicsManage():
    return render_template("graphics/myGraphicsManage.html")

@app.route('/addGraphics')
def addGraphics():
    treeData = getGraphicsTreeData()
    return render_template("graphics/addGraphics.html", treeData=treeData)
@app.route('/uploadImage', methods=['POST', 'GET'])
def uploadImage():
    if 'file' not in request.files:
        print('No file part')
        return redirect(request.url)
    f = request.files['file']
    # 首先导入七牛云的包
    from qiniu import Auth, put_data
    # 需要填写你的 Access Key 和 Secret Key
    access_key = '-7nAHhIriIPcXvEbmuuc5-r84L8XDL2_hCcmeNXi'
    secret_key = 'u57OARTTCUQg7F4hJPq3ATSr-PveVXpIWse71bQb'
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'industry3app'
    # 上传后保存的文件名
    # key = 'my-python-logo.png'
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)
    # 要上传文件的本地路径
    # localfile = './sync/bbb.jpg'

    # ret保存的是文件哈希值 和  文件名   由于我们这里没有指定文件，所以文件名和哈希值一样
    # info 是一些存储信息
    ret, info = put_data(token, None, f.read())
    fileUrl = "http://qxj20y6xn.bkt.clouddn.com"+'/'+ret['key']
    return jsonify({'fileUrl':fileUrl, 'key':ret['key'], 'status':"1"})

@app.route('/saveMyGraphics', methods=['POST', 'GET'])
def saveMyGraphics():
    imageName = request.form.get('imageName')
    type = request.form.get('type')
    title = request.form.get('title')
    imageUrl = request.form.get('imageUrl')
    imageId = request.form.get('imageId')
    creatDate = datetime.now()
    provider = current_user.username
    status = 0
    storageNum = 0
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "INSERT INTO  graphics (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{})".format(
            imageName, type,title,imageUrl,imageId,provider,creatDate, status,storageNum)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '该图案已存在!'})
#款式手稿
@app.route('/styles')
def styles():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from styles "
    count = cursor.execute(sql)
    count = { "count": count}
    results = getStylesTreeData()
    db.commit()
    db.close()
    return render_template("styles/styles.html", count= count, stylesFenleis = results, username= session.get("username"))
@app.route('/stylesList', methods=['POST', 'GET'])
def stylesList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    keyValues = request.args.get("keyValues")
    print(keyValues)
    if keyValues!=None and keyValues!="" :
        keyValues=tuple(str(keyValues).split(","))
    else:
        keyValues = []
    query = request.args.get("q")
    start = (page-1)*size
    print(start, size)
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    sql = "select * from styles WHERE  status = 1"
    if query !=None and query !="":
        if len(keyValues) == 0:
            sql="select * from styles WHERE type like '{}' or provider like '{}' and status = 1".format(query, query)
        else:
            sql = "select * from styles WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
    if len(keyValues)>0:
        if query != None and query != "":
            sql= "select * from styles WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
        else:
            sql= "select * from styles WHERE type in {} and status = 1".format(keyValues)

    sql1 = sql +" order by creatDate desc" +" limit {}, {}".format(start, size)
    sql2 = sql +" order by creatDate desc"
    print(sql1)
    print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)

    glist = sql_fetch_json(cursor1)
    results = {"data":glist, "count":count}
    db.commit()
    db.close()
    return render_template("styles/stylesList.html", styleslist= results)
@app.route('/updateStylesStaus', methods=['POST', 'GET'])
def updateStylesStaus():
    status = request.form.get('status')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update styles set status={} where imageId ='{}'".format(int(status),imageId)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '修改成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '修改失败!'})
##款式分类
@app.route('/stylesFenlei')
def stylesFenlei():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from stylesfenlei"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    # result = json.dumps(treeData,ensure_ascii=False)
    return render_template("styles/stylesFenlei.html", treeData= treeData)
@app.route('/saveStyleFenleiRoot', methods=['POST', 'GET'])
def saveStyleFenleiRoot():
    title = request.form.get("title")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from stylesfenlei WHERE father = -1"
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = "fenlei-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = "fenlei-" + str(max(V) + 1)
    sql1 = "INSERT INTO  stylesfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, -1)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})


@app.route('/saveStyleFenleiSecond', methods=['POST', 'GET'])
def saveStyleFenleiSecond():
    title  = request.form.get("title")
    father = request.form.get("father")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from stylesfenlei WHERE father = '{}'".format(father)
    print(sql)
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = father + "-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = father + "-" + str(max(V) + 1)
    sql1 = "INSERT INTO  stylesfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, father)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        treeData = getStylesTreeData()
        print(treeData)
        return jsonify({'status': '1', 'msg': '保存成功!', 'treeData':treeData})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})
@app.route('/updateStylesFenlei', methods=['POST', 'GET'])
def updateStylesFenlei():
    fenleis  = request.form.get('fenleidata')
    fenleis = json.loads(fenleis)
    db = pymysql.connect(**config)
    try:
        for f in fenleis:
            cursor = db.cursor()
            title = f["title"]
            value = f["value"]
            sql = "update stylesfenlei set title='{}' where value ='{}'".format(title, value)
            print(sql)
            cursor.execute(sql)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '保存失败!'})
@app.route('/deleteStylesFenlei', methods=['POST','GET'])
def deleteStylesFenlei():
    delId = request.form.get('delId')
    db = pymysql.connect(**config)
    sql1 = "select father from stylesfenlei WHERE value ='{}'".format(delId)
    sql2 = "delete from stylesfenlei where value ='{}'".format(delId)

    print(sql1)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()
    cursor1.execute(sql1)
    result = sql_fetch_json(cursor1)
    father = result[0]['father']
    sql3 = "delete from stylesfenlei where father ='{}'".format(delId)

    try:
        if father == '-1':
            cursor2.execute(sql2)
            cursor3.execute(sql3)
            print(sql2)
            print(sql3)
            db.commit()
        else:
            cursor2.execute(sql2)
            print(sql2)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})

def getStylesTreeData():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from stylesfenlei"
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return treeData

##款式手稿收藏
@app.route('/addStylecStorage', methods=['POST', 'GET'])
def addStylecStorage():
    status = request.form.get('storageStatus')
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)

    sql = "select storageNum from styles where imageId = '{}'".format(imageId)
    cursor = db.cursor()
    cursor.execute(sql)
    storageNums = sql_fetch_json(cursor)
    storageNum = int(storageNums[0]["storageNum"])

    if status =="1":
        try:
            cursor1 = db.cursor()
            sql1 = "select * from styles where imageId = '{}'".format(imageId)
            print(sql1)
            cursor1.execute(sql1)
            graphics = sql_fetch_json(cursor1)
            graphic = graphics[0]
            storageId = username + imageId
            sql2 = "INSERT INTO  stylesStorage (username,imageId, imageUrl, title, type, provider, creatDate,storageId ) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')".format(
                                            username, imageId,graphic['imageUrl'],
                                           graphic['title'],graphic['type'],
                                           graphic['provider'],graphic['creatDate'], storageId)
            print(sql2)
            cursor2 = db.cursor()
            cursor2.execute(sql2)

            storageNum = storageNum + 1
            sql2_ = "update  styles set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor2_ = db.cursor()
            cursor2_.execute(sql2_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '收藏成功!'})
        except Exception:
            return jsonify({'status': '0', 'msg': '该数据已收藏!'})
    if status =="0":
        try:
            cursor3 = db.cursor()
            sql3 = "delete from stylesStorage where imageId ='{}'".format(imageId)
            cursor3.execute(sql3)

            storageNum = storageNum - 1
            sql3_ = "update  styles set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor3_ = db.cursor()
            cursor3_.execute(sql3_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '取消收藏!'})
        except Exception:

            return jsonify({'status': '0', 'msg': '取消收藏失败!'})

@app.route('/getMySorageStylesById', methods=['POST', 'GET'])
def getMySorageStylesById():
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "select * from stylesStorage where username='{}' and imageId ='{}'".format(username,imageId)
        print(sql)
        count = cursor.execute(sql)
        db.commit()
        db.close()
        if count >0:
            return jsonify({'status': '1'})
        else:
            return jsonify({'status': '0'})
    except Exception:

        return jsonify({'status': '0'})

@app.route('/stylesStorageManage')
def stylesStorageManage():
    return render_template("styles/stylesStorageManage.html")
@app.route('/stylesStorageManageList', methods=['POST', 'GET'])
def stylesStorageManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from stylesStorage where username = '{}' limit {}, {} ".format(username, start, size)
        sql2 = "select * from stylesStorage where username = '{}'".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from stylesStorage where username = '{}' and type like '{}' limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from stylesStorage where username = '{}' and type like '{}' ".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#系统款式手稿管理
@app.route('/sysStylesManage')
def sysStylesManage():
    return render_template("styles/stylesManage.html")

@app.route('/stylesManageList', methods=['POST', 'GET'])
def stylesManageList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from styles order by creatDate desc limit {}, {} ".format(start, size)
        sql2 = "select * from styles order by creatDate desc"
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from styles where type like '{}' order by creatDate desc limit {}, {} ".format(query, start, size)
        sql2 = "select * from styles where type like '{}' order by creatDate desc ".format(query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#我的款式手稿
@app.route('/myStylesManageList', methods=['POST', 'GET'])
def myStylesManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from styles where provider = '{}' order by creatDate desc limit {}, {} ".format(username, start, size)
        sql2 = "select * from styles where provider = '{}' order by creatDate desc".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from styles where provider = '{}' and type like '{}' order by creatDate desc limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from styles where provider = '{}' and type like '{}' order by creatDate desc".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/myStylesManage')
def myStylesManage():
    return render_template("styles/myStylesManage.html")

@app.route('/addStyles')
def addStyles():
    treeData = getStylesTreeData()
    return render_template("styles/addStyles.html", treeData=treeData)
@app.route('/saveMyStyles', methods=['POST', 'GET'])
def saveMyStyles():
    imageName = request.form.get('imageName')
    type = request.form.get('type')
    title = request.form.get('title')
    imageUrl = request.form.get('imageUrl')
    imageId = request.form.get('imageId')
    creatDate = datetime.now()
    provider = current_user.username
    status = 0
    storageNum = 0
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "INSERT INTO  styles (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{})".format(
            imageName, type,title,imageUrl,imageId,provider,creatDate, status,storageNum)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '该数据已存在!'})

#款式细节
@app.route('/details')
def details():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from details "
    count = cursor.execute(sql)
    count = { "count": count}
    results = getDetailsTreeData()
    db.commit()
    db.close()
    return render_template("details/details.html", count= count, detailsFenleis = results, username= session.get("username"))
@app.route('/detailsList', methods=['POST', 'GET'])
def detailsList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    keyValues = request.args.get("keyValues")
    print(keyValues)
    if keyValues!=None and keyValues!="" :
        keyValues=tuple(str(keyValues).split(","))
    else:
        keyValues = []
    query = request.args.get("q")
    start = (page-1)*size
    print(start, size)
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    sql = "select * from details WHERE  status = 1"
    if query !=None and query !="":
        if len(keyValues) == 0:
            sql="select * from details WHERE type like '{}' or provider like '{}' and status = 1".format(query, query)
        else:
            sql = "select * from details WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
    if len(keyValues)>0:
        if query != None and query != "":
            sql= "select * from details WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
        else:
            sql= "select * from details WHERE type in {} and status = 1".format(keyValues)

    sql1 = sql +" order by creatDate desc" +" limit {}, {}".format(start, size)
    sql2 = sql +" order by creatDate desc"
    print(sql1)
    print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)

    glist = sql_fetch_json(cursor1)
    results = {"data":glist, "count":count}
    db.commit()
    db.close()
    return render_template("details/detailsList.html", detailslist= results)
@app.route('/updateDetailsStaus', methods=['POST', 'GET'])
def updateDetailsStaus():
    status = request.form.get('status')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update details set status={} where imageId ='{}'".format(int(status),imageId)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '修改成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '修改失败!'})
##款式细节分类
@app.route('/detailsFenlei')
def detailsFenlei():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from detailsfenlei"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    # result = json.dumps(treeData,ensure_ascii=False)
    return render_template("details/detailsFenlei.html", treeData= treeData)
@app.route('/saveDetailsFenleiRoot', methods=['POST', 'GET'])
def saveDetailsFenleiRoot():
    title = request.form.get("title")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from detailsfenlei WHERE father = -1"
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = "fenlei-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = "fenlei-" + str(max(V) + 1)
    sql1 = "INSERT INTO  detailsfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, -1)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})


@app.route('/saveDetailsFenleiSecond', methods=['POST', 'GET'])
def saveDetailsFenleiSecond():
    title  = request.form.get("title")
    father = request.form.get("father")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from detailsfenlei WHERE father = '{}'".format(father)
    print(sql)
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = father + "-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = father + "-" + str(max(V) + 1)
    sql1 = "INSERT INTO  detailsfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, father)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        treeData = getDetailsTreeData()
        print(treeData)
        return jsonify({'status': '1', 'msg': '保存成功!', 'treeData':treeData})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})
@app.route('/updateDetailsFenlei', methods=['POST', 'GET'])
def updateDetailsFenlei():
    fenleis  = request.form.get('fenleidata')
    fenleis = json.loads(fenleis)
    db = pymysql.connect(**config)
    try:
        for f in fenleis:
            cursor = db.cursor()
            title = f["title"]
            value = f["value"]
            sql = "update detailsfenlei set title='{}' where value ='{}'".format(title, value)
            print(sql)
            cursor.execute(sql)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '保存失败!'})
@app.route('/deleteDetailsFenlei', methods=['POST','GET'])
def deleteDetailsFenlei():
    delId = request.form.get('delId')
    db = pymysql.connect(**config)
    sql1 = "select father from detailsfenlei WHERE value ='{}'".format(delId)
    sql2 = "delete from detailsfenlei where value ='{}'".format(delId)

    print(sql1)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()
    cursor1.execute(sql1)
    result = sql_fetch_json(cursor1)
    father = result[0]['father']
    sql3 = "delete from detailsfenlei where father ='{}'".format(delId)

    try:
        if father == '-1':
            cursor2.execute(sql2)
            cursor3.execute(sql3)
            print(sql2)
            print(sql3)
            db.commit()
        else:
            cursor2.execute(sql2)
            print(sql2)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})

def getDetailsTreeData():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from detailsfenlei"
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return treeData

##款式细节收藏
@app.route('/addDetailsStorage', methods=['POST', 'GET'])
def addDetailsStorage():
    status = request.form.get('storageStatus')
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)

    sql = "select storageNum from details where imageId = '{}'".format(imageId)
    cursor = db.cursor()
    cursor.execute(sql)
    storageNums = sql_fetch_json(cursor)
    storageNum = int(storageNums[0]["storageNum"])

    if status =="1":
        try:
            cursor1 = db.cursor()
            sql1 = "select * from details where imageId = '{}'".format(imageId)
            print(sql1)
            cursor1.execute(sql1)
            graphics = sql_fetch_json(cursor1)
            graphic = graphics[0]
            storageId = username + imageId
            sql2 = "INSERT INTO  detailsstorage (username,imageId, imageUrl, title, type, provider, creatDate,storageId ) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')".format(
                                            username, imageId,graphic['imageUrl'],
                                           graphic['title'],graphic['type'],
                                           graphic['provider'],graphic['creatDate'], storageId)
            print(sql2)
            cursor2 = db.cursor()
            cursor2.execute(sql2)

            storageNum = storageNum + 1
            sql2_ = "update  details set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor2_ = db.cursor()
            cursor2_.execute(sql2_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '收藏成功!'})
        except Exception:
            return jsonify({'status': '0', 'msg': '该数据已收藏!'})
    if status =="0":
        try:
            cursor3 = db.cursor()
            sql3 = "delete from detailsstorage where imageId ='{}'".format(imageId)
            cursor3.execute(sql3)

            storageNum = storageNum - 1
            sql3_ = "update  details set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor3_ = db.cursor()
            cursor3_.execute(sql3_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '取消收藏!'})
        except Exception:

            return jsonify({'status': '0', 'msg': '取消收藏失败!'})

@app.route('/getMySorageDetailsById', methods=['POST', 'GET'])
def getMySorageDetailsById():
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "select * from detailsstorage where username='{}' and imageId ='{}'".format(username,imageId)
        print(sql)
        count = cursor.execute(sql)
        db.commit()
        db.close()
        if count >0:
            return jsonify({'status': '1'})
        else:
            return jsonify({'status': '0'})
    except Exception:

        return jsonify({'status': '0'})

@app.route('/detailsStorageManage')
def detailsStorageManage():
    return render_template("details/detailsStorageManage.html")
@app.route('/detailsStorageManageList', methods=['POST', 'GET'])
def detailsStorageManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from detailsstorage where username = '{}' limit {}, {} ".format(username, start, size)
        sql2 = "select * from detailsstorage where username = '{}'".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from detailsstorage where username = '{}' and type like '{}' limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from detailsstorage where username = '{}' and type like '{}' ".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#系统款式细节管理
@app.route('/sysDetailsManage')
def sysDetailsManage():
    return render_template("details/detailsManage.html")

@app.route('/detailsManageList', methods=['POST', 'GET'])
def detailsManageList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from details order by creatDate desc limit {}, {} ".format(start, size)
        sql2 = "select * from details order by creatDate desc"
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from details where type like '{}' order by creatDate desc limit {}, {} ".format(query, start, size)
        sql2 = "select * from details where type like '{}' order by creatDate desc ".format(query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#我的款式手稿
@app.route('/myDetailsManageList', methods=['POST', 'GET'])
def myDetailsManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from details where provider = '{}' order by creatDate desc limit {}, {} ".format(username, start, size)
        sql2 = "select * from details where provider = '{}' order by creatDate desc".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from details where provider = '{}' and type like '{}' order by creatDate desc limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from details where provider = '{}' and type like '{}' order by creatDate desc".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/myDetailsManage')
def myDetailsManage():
    return render_template("details/myDetailsManage.html")

@app.route('/addDetails')
def addDetails():
    treeData = getDetailsTreeData()
    return render_template("details/addDetails.html", treeData=treeData)
@app.route('/saveMyDetails', methods=['POST', 'GET'])
def saveMyDetails():
    imageName = request.form.get('imageName')
    type = request.form.get('type')
    title = request.form.get('title')
    imageUrl = request.form.get('imageUrl')
    imageId = request.form.get('imageId')
    creatDate = datetime.now()
    provider = current_user.username
    status = 0
    storageNum = 0
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "INSERT INTO  details (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{})".format(
            imageName, type,title,imageUrl,imageId,provider,creatDate, status,storageNum)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '该数据已存在!'})
#面料
@app.route('/fabrics')
def fabrics():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from fabrics "
    count = cursor.execute(sql)
    count = { "count": count}
    results = getFabricsTreeData()
    db.commit()
    db.close()
    return render_template("fabrics/fabrics.html", count= count, fabricsFenleis = results, username= session.get("username"))
@app.route('/fabricsList', methods=['POST', 'GET'])
def fabricsList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    keyValues = request.args.get("keyValues")
    print(keyValues)
    if keyValues!=None and keyValues!="" :
        keyValues=tuple(str(keyValues).split(","))
    else:
        keyValues = []
    query = request.args.get("q")
    start = (page-1)*size
    print(start, size)
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    sql = "select * from fabrics WHERE  status = 1"
    if query !=None and query !="":
        if len(keyValues) == 0:
            sql="select * from fabrics WHERE type like '{}' or provider like '{}' and status = 1".format(query, query)
        else:
            sql = "select * from fabrics WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
    if len(keyValues)>0:
        if query != None and query != "":
            sql= "select * from fabrics WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
        else:
            sql= "select * from fabrics WHERE type in {} and status = 1".format(keyValues)

    sql1 = sql +" order by creatDate desc" +" limit {}, {}".format(start, size)
    sql2 = sql +" order by creatDate desc"
    print(sql1)
    print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)

    glist = sql_fetch_json(cursor1)
    results = {"data":glist, "count":count}
    db.commit()
    db.close()
    return render_template("fabrics/fabricsList.html", fabricslist= results)
@app.route('/updateFabricsStaus', methods=['POST', 'GET'])
def updateFabricsStaus():
    status = request.form.get('status')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update fabrics set status={} where imageId ='{}'".format(int(status),imageId)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '修改成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '修改失败!'})
##面料分类
@app.route('/fabricsFenlei')
def fabricsFenlei():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from fabricsfenlei"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    # result = json.dumps(treeData,ensure_ascii=False)
    return render_template("fabrics/fabricsFenlei.html", treeData= treeData)
@app.route('/saveFabricsFenleiRoot', methods=['POST', 'GET'])
def saveFabricsFenleiRoot():
    title = request.form.get("title")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from fabricsfenlei WHERE father = -1"
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = "fenlei-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = "fenlei-" + str(max(V) + 1)
    sql1 = "INSERT INTO  fabricsfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, -1)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})


@app.route('/saveFabricsFenleiSecond', methods=['POST', 'GET'])
def saveFabricsFenleiSecond():
    title  = request.form.get("title")
    father = request.form.get("father")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from fabricsfenlei WHERE father = '{}'".format(father)
    print(sql)
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = father + "-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = father + "-" + str(max(V) + 1)
    sql1 = "INSERT INTO  fabricsfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, father)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        treeData = getFabricsTreeData()
        print(treeData)
        return jsonify({'status': '1', 'msg': '保存成功!', 'treeData':treeData})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})
@app.route('/updateFabricsFenlei', methods=['POST', 'GET'])
def updateFabricsFenlei():
    fenleis  = request.form.get('fenleidata')
    fenleis = json.loads(fenleis)
    db = pymysql.connect(**config)
    try:
        for f in fenleis:
            cursor = db.cursor()
            title = f["title"]
            value = f["value"]
            sql = "update fabricsfenlei set title='{}' where value ='{}'".format(title, value)
            print(sql)
            cursor.execute(sql)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '保存失败!'})
@app.route('/deleteFabricsFenlei', methods=['POST','GET'])
def deleteFabricsFenlei():
    delId = request.form.get('delId')
    db = pymysql.connect(**config)
    sql1 = "select father from fabricsfenlei WHERE value ='{}'".format(delId)
    sql2 = "delete from fabricsfenlei where value ='{}'".format(delId)

    print(sql1)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()
    cursor1.execute(sql1)
    result = sql_fetch_json(cursor1)
    father = result[0]['father']
    sql3 = "delete from fabricsfenlei where father ='{}'".format(delId)

    try:
        if father == '-1':
            cursor2.execute(sql2)
            cursor3.execute(sql3)
            print(sql2)
            print(sql3)
            db.commit()
        else:
            cursor2.execute(sql2)
            print(sql2)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})

def getFabricsTreeData():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from fabricsfenlei"
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return treeData

##面料收藏
@app.route('/addFabricsStorage', methods=['POST', 'GET'])
def addFabricsStorage():
    status = request.form.get('storageStatus')
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)

    sql = "select storageNum from fabrics where imageId = '{}'".format(imageId)
    cursor = db.cursor()
    cursor.execute(sql)
    storageNums = sql_fetch_json(cursor)
    storageNum = int(storageNums[0]["storageNum"])

    if status =="1":
        try:
            cursor1 = db.cursor()
            sql1 = "select * from fabrics where imageId = '{}'".format(imageId)
            print(sql1)
            cursor1.execute(sql1)
            graphics = sql_fetch_json(cursor1)
            graphic = graphics[0]
            storageId = username + imageId
            sql2 = "INSERT INTO  fabricsstorage (username,imageId, imageUrl, title, type, provider, creatDate,storageId ) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')".format(
                                            username, imageId,graphic['imageUrl'],
                                           graphic['title'],graphic['type'],
                                           graphic['provider'],graphic['creatDate'], storageId)
            print(sql2)
            cursor2 = db.cursor()
            cursor2.execute(sql2)

            storageNum = storageNum + 1
            sql2_ = "update  fabrics set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor2_ = db.cursor()
            cursor2_.execute(sql2_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '收藏成功!'})
        except Exception:
            return jsonify({'status': '0', 'msg': '该数据已收藏!'})
    if status =="0":
        try:
            cursor3 = db.cursor()
            sql3 = "delete from fabricsstorage where imageId ='{}'".format(imageId)
            cursor3.execute(sql3)

            storageNum = storageNum - 1
            sql3_ = "update  fabrics set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor3_ = db.cursor()
            cursor3_.execute(sql3_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '取消收藏!'})
        except Exception:

            return jsonify({'status': '0', 'msg': '取消收藏失败!'})

@app.route('/getMySorageFabricsById', methods=['POST', 'GET'])
def getMySorageFabricsById():
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "select * from fabricsstorage where username='{}' and imageId ='{}'".format(username,imageId)
        print(sql)
        count = cursor.execute(sql)
        db.commit()
        db.close()
        if count >0:
            return jsonify({'status': '1'})
        else:
            return jsonify({'status': '0'})
    except Exception:

        return jsonify({'status': '0'})

@app.route('/fabricsStorageManage')
def fabricsStorageManage():
    return render_template("fabrics/fabricsStorageManage.html")
@app.route('/fabricsStorageManageList', methods=['POST', 'GET'])
def fabricsStorageManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from fabricsstorage where username = '{}' limit {}, {} ".format(username, start, size)
        sql2 = "select * from fabricsstorage where username = '{}'".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from fabricsstorage where username = '{}' and type like '{}' limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from fabricsstorage where username = '{}' and type like '{}' ".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#系统款式细节管理
@app.route('/sysFabricsManage')
def sysFabricsManage():
    return render_template("fabrics/fabricsManage.html")

@app.route('/fabricsManageList', methods=['POST', 'GET'])
def fabricsManageList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from fabrics order by creatDate desc limit {}, {} ".format(start, size)
        sql2 = "select * from fabrics order by creatDate desc"
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from fabrics where type like '{}' order by creatDate desc limit {}, {} ".format(query, start, size)
        sql2 = "select * from fabrics where type like '{}' order by creatDate desc ".format(query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#我的款式手稿
@app.route('/myFabricsManageList', methods=['POST', 'GET'])
def myFabricsManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from fabrics where provider = '{}' order by creatDate desc limit {}, {} ".format(username, start, size)
        sql2 = "select * from fabrics where provider = '{}' order by creatDate desc".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from fabrics where provider = '{}' and type like '{}' order by creatDate desc limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from fabrics where provider = '{}' and type like '{}' order by creatDate desc".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/myFabricsManage')
def myFabricsManage():
    return render_template("fabrics/myFabricsManage.html")

@app.route('/addFabrics')
def addFabrics():
    treeData = getFabricsTreeData()
    return render_template("fabrics/addFabrics.html", treeData=treeData)
@app.route('/saveMyFabrics', methods=['POST', 'GET'])
def saveMyFabrics():
    imageName = request.form.get('imageName')
    type = request.form.get('type')
    title = request.form.get('title')
    imageUrl = request.form.get('imageUrl')
    imageId = request.form.get('imageId')
    creatDate = datetime.now()
    provider = current_user.username
    status = 0
    storageNum = 0
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "INSERT INTO  fabrics (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{})".format(
            imageName, type,title,imageUrl,imageId,provider,creatDate, status,storageNum)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '该数据已存在!'})

#服饰品
@app.route('/accessories')
def accessories():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from accessories "
    count = cursor.execute(sql)
    count = { "count": count}
    results = getAccessoriesTreeData()
    db.commit()
    db.close()
    return render_template("accessories/accessories.html", count= count, accessoriesFenleis = results, username= session.get("username"))
@app.route('/accessoriesList', methods=['POST', 'GET'])
def accessoriesList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    keyValues = request.args.get("keyValues")
    print(keyValues)
    if keyValues!=None and keyValues!="" :
        keyValues=tuple(str(keyValues).split(","))
    else:
        keyValues = []
    query = request.args.get("q")
    start = (page-1)*size
    print(start, size)
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    sql = "select * from accessories WHERE  status = 1"
    if query !=None and query !="":
        if len(keyValues) == 0:
            sql="select * from accessories WHERE type like '{}' or provider like '{}' and status = 1".format(query, query)
        else:
            sql = "select * from accessories WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
    if len(keyValues)>0:
        if query != None and query != "":
            sql= "select * from accessories WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
        else:
            sql= "select * from accessories WHERE type in {} and status = 1".format(keyValues)

    sql1 = sql +" order by creatDate desc" +" limit {}, {}".format(start, size)
    sql2 = sql +" order by creatDate desc"
    print(sql1)
    print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)

    glist = sql_fetch_json(cursor1)
    results = {"data":glist, "count":count}
    db.commit()
    db.close()
    return render_template("accessories/accessoriesList.html", accessorieslist= results)
@app.route('/updateAccessoriesStaus', methods=['POST', 'GET'])
def updateAccessoriesStaus():
    status = request.form.get('status')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update accessories set status={} where imageId ='{}'".format(int(status),imageId)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '修改成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '修改失败!'})
##面料分类
@app.route('/accessoriesFenlei')
def accessoriesFenlei():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from accessoriesfenlei"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    # result = json.dumps(treeData,ensure_ascii=False)
    return render_template("accessories/accessoriesFenlei.html", treeData= treeData)
@app.route('/saveAccessoriesFenleiRoot', methods=['POST', 'GET'])
def saveAccessoriesFenleiRoot():
    title = request.form.get("title")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from accessoriesfenlei WHERE father = -1"
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = "fenlei-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = "fenlei-" + str(max(V) + 1)
    sql1 = "INSERT INTO  accessoriesfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, -1)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})


@app.route('/saveAccessoriesFenleiSecond', methods=['POST', 'GET'])
def saveAccessoriesFenleiSecond():
    title  = request.form.get("title")
    father = request.form.get("father")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from accessoriesfenlei WHERE father = '{}'".format(father)
    print(sql)
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = father + "-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = father + "-" + str(max(V) + 1)
    sql1 = "INSERT INTO  accessoriesfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, father)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        treeData = getAccessoriesTreeData()
        print(treeData)
        return jsonify({'status': '1', 'msg': '保存成功!', 'treeData':treeData})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})
@app.route('/updateAccessoriesFenlei', methods=['POST', 'GET'])
def updateAccessoriesFenlei():
    fenleis  = request.form.get('fenleidata')
    fenleis = json.loads(fenleis)
    db = pymysql.connect(**config)
    try:
        for f in fenleis:
            cursor = db.cursor()
            title = f["title"]
            value = f["value"]
            sql = "update accessoriesfenlei set title='{}' where value ='{}'".format(title, value)
            print(sql)
            cursor.execute(sql)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '保存失败!'})
@app.route('/deleteAccessoriesFenlei', methods=['POST','GET'])
def deleteAccessoriesFenlei():
    delId = request.form.get('delId')
    db = pymysql.connect(**config)
    sql1 = "select father from accessoriesfenlei WHERE value ='{}'".format(delId)
    sql2 = "delete from accessoriesfenlei where value ='{}'".format(delId)

    print(sql1)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()
    cursor1.execute(sql1)
    result = sql_fetch_json(cursor1)
    father = result[0]['father']
    sql3 = "delete from accessoriesfenlei where father ='{}'".format(delId)

    try:
        if father == '-1':
            cursor2.execute(sql2)
            cursor3.execute(sql3)
            print(sql2)
            print(sql3)
            db.commit()
        else:
            cursor2.execute(sql2)
            print(sql2)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})

def getAccessoriesTreeData():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from accessoriesfenlei"
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return treeData

##面料收藏
@app.route('/addAccessoriesStorage', methods=['POST', 'GET'])
def addAccessoriesStorage():
    status = request.form.get('storageStatus')
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)

    sql = "select storageNum from accessories where imageId = '{}'".format(imageId)
    cursor = db.cursor()
    cursor.execute(sql)
    storageNums = sql_fetch_json(cursor)
    storageNum = int(storageNums[0]["storageNum"])

    if status =="1":
        try:
            cursor1 = db.cursor()
            sql1 = "select * from accessories where imageId = '{}'".format(imageId)
            print(sql1)
            cursor1.execute(sql1)
            graphics = sql_fetch_json(cursor1)
            graphic = graphics[0]
            storageId = username + imageId
            sql2 = "INSERT INTO  accessoriesstorage (username,imageId, imageUrl, title, type, provider, creatDate,storageId ) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')".format(
                                            username, imageId,graphic['imageUrl'],
                                           graphic['title'],graphic['type'],
                                           graphic['provider'],graphic['creatDate'], storageId)
            print(sql2)
            cursor2 = db.cursor()
            cursor2.execute(sql2)

            storageNum = storageNum + 1
            sql2_ = "update  accessories set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor2_ = db.cursor()
            cursor2_.execute(sql2_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '收藏成功!'})
        except Exception:
            return jsonify({'status': '0', 'msg': '该数据已收藏!'})
    if status =="0":
        try:
            cursor3 = db.cursor()
            sql3 = "delete from accessoriesstorage where imageId ='{}'".format(imageId)
            cursor3.execute(sql3)

            storageNum = storageNum - 1
            sql3_ = "update  accessories set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor3_ = db.cursor()
            cursor3_.execute(sql3_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '取消收藏!'})
        except Exception:

            return jsonify({'status': '0', 'msg': '取消收藏失败!'})

@app.route('/getMySorageAccessoriesById', methods=['POST', 'GET'])
def getMySorageAccessoriesById():
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "select * from accessoriesstorage where username='{}' and imageId ='{}'".format(username,imageId)
        print(sql)
        count = cursor.execute(sql)
        db.commit()
        db.close()
        if count >0:
            return jsonify({'status': '1'})
        else:
            return jsonify({'status': '0'})
    except Exception:

        return jsonify({'status': '0'})

@app.route('/accessoriesStorageManage')
def accessoriesStorageManage():
    return render_template("accessories/accessoriesStorageManage.html")
@app.route('/accessoriesStorageManageList', methods=['POST', 'GET'])
def accessoriesStorageManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from accessoriesstorage where username = '{}' limit {}, {} ".format(username, start, size)
        sql2 = "select * from accessoriesstorage where username = '{}'".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from accessoriesstorage where username = '{}' and type like '{}' limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from accessoriesstorage where username = '{}' and type like '{}' ".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#系统款式细节管理
@app.route('/sysAccessoriesManage')
def sysAccessoriesManage():
    return render_template("accessories/accessoriesManage.html")

@app.route('/accessoriesManageList', methods=['POST', 'GET'])
def accessoriesManageList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from accessories order by creatDate desc limit {}, {} ".format(start, size)
        sql2 = "select * from accessories order by creatDate desc"
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from accessories where type like '{}' order by creatDate desc limit {}, {} ".format(query, start, size)
        sql2 = "select * from accessories where type like '{}' order by creatDate desc ".format(query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#我的款式手稿
@app.route('/myAccessoriesManageList', methods=['POST', 'GET'])
def myAccessoriesManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from accessories where provider = '{}' order by creatDate desc limit {}, {} ".format(username, start, size)
        sql2 = "select * from accessories where provider = '{}' order by creatDate desc".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from accessories where provider = '{}' and type like '{}' order by creatDate desc limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from accessories where provider = '{}' and type like '{}' order by creatDate desc".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/myAccessoriesManage')
def myAccessoriesManage():
    return render_template("accessories/myaccessoriesManage.html")

@app.route('/addAccessories')
def addAccessories():
    treeData = getAccessoriesTreeData()
    return render_template("accessories/addAccessories.html", treeData=treeData)
@app.route('/saveMyAccessories', methods=['POST', 'GET'])
def saveMyAccessories():
    imageName = request.form.get('imageName')
    type = request.form.get('type')
    title = request.form.get('title')
    imageUrl = request.form.get('imageUrl')
    imageId = request.form.get('imageId')
    creatDate = datetime.now()
    provider = current_user.username
    status = 0
    storageNum = 0
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "INSERT INTO  accessories (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{})".format(
            imageName, type,title,imageUrl,imageId,provider,creatDate, status,storageNum)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '该数据已存在!'})



#灵感源
@app.route('/inspiration')
def inspiration():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from inspiration "
    count = cursor.execute(sql)
    count = { "count": count}
    results = getInspirationTreeData()
    db.commit()
    db.close()
    return render_template("inspiration/inspiration.html", count= count, inspirationFenleis = results, username= session.get("username"))
@app.route('/inspirationList', methods=['POST', 'GET'])
def inspirationList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    keyValues = request.args.get("keyValues")
    print(keyValues)
    if keyValues!=None and keyValues!="" :
        keyValues=tuple(str(keyValues).split(","))
    else:
        keyValues = []
    query = request.args.get("q")
    start = (page-1)*size
    print(start, size)
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    sql = "select * from inspiration WHERE  status = 1"
    if query !=None and query !="":
        if len(keyValues) == 0:
            sql="select * from inspiration WHERE type like '{}' or provider like '{}' and status = 1".format(query, query)
        else:
            sql = "select * from inspiration WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
    if len(keyValues)>0:
        if query != None and query != "":
            sql= "select * from inspiration WHERE type in {} or type like '{}' or provider like '{} and status = 1".format(keyValues, query, query)
        else:
            sql= "select * from inspiration WHERE type in {} and status = 1".format(keyValues)

    sql1 = sql +" order by creatDate desc" +" limit {}, {}".format(start, size)
    sql2 = sql +" order by creatDate desc"
    print(sql1)
    print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)

    glist = sql_fetch_json(cursor1)
    results = {"data":glist, "count":count}
    db.commit()
    db.close()
    return render_template("inspiration/inspirationList.html", inspirationlist= results)
@app.route('/updateInspirationStaus', methods=['POST', 'GET'])
def updateInspirationStaus():
    status = request.form.get('status')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update inspiration set status={} where imageId ='{}'".format(int(status),imageId)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '修改成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '修改失败!'})
##面料分类
@app.route('/inspirationFenlei')
def inspirationFenlei():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from inspirationfenlei"
    print(sql)
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    # result = json.dumps(treeData,ensure_ascii=False)
    return render_template("inspiration/inspirationFenlei.html", treeData= treeData)
@app.route('/saveInspirationFenleiRoot', methods=['POST', 'GET'])
def saveInspirationFenleiRoot():
    title = request.form.get("title")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from inspirationfenlei WHERE father = -1"
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = "fenlei-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = "fenlei-" + str(max(V) + 1)
    sql1 = "INSERT INTO  inspirationfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, -1)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})


@app.route('/saveInspirationFenleiSecond', methods=['POST', 'GET'])
def saveInspirationFenleiSecond():
    title  = request.form.get("title")
    father = request.form.get("father")
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select value from inspirationfenlei WHERE father = '{}'".format(father)
    print(sql)
    cursor.execute(sql)
    result = sql_fetch_json(cursor)
    value = ""
    if len(result) == 0:
        value = father + "-" + str(1)
    else:
        V = []
        for r in result:
            V.append(int(r["value"].split("-")[-1]))
        value = father + "-" + str(max(V) + 1)
    sql1 = "INSERT INTO  inspirationfenlei (value,title, father )VALUES ('{}','{}','{}')".format(value, title, father)
    print(sql1)

    try:
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        db.commit()
        db.close()
        treeData = getInspirationTreeData()
        print(treeData)
        return jsonify({'status': '1', 'msg': '保存成功!', 'treeData':treeData})
    except Exception:
        return jsonify({'status': '0','msg': '该分类名称已存在!'})
@app.route('/updateInspirationFenlei', methods=['POST', 'GET'])
def updateInspirationFenlei():
    fenleis  = request.form.get('fenleidata')
    fenleis = json.loads(fenleis)
    db = pymysql.connect(**config)
    try:
        for f in fenleis:
            cursor = db.cursor()
            title = f["title"]
            value = f["value"]
            sql = "update inspirationfenlei set title='{}' where value ='{}'".format(title, value)
            print(sql)
            cursor.execute(sql)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:

        return jsonify({'status': '0', 'msg': '保存失败!'})
@app.route('/deleteInspirationFenlei', methods=['POST','GET'])
def deleteInspirationFenlei():
    delId = request.form.get('delId')
    db = pymysql.connect(**config)
    sql1 = "select father from inspirationfenlei WHERE value ='{}'".format(delId)
    sql2 = "delete from inspirationfenlei where value ='{}'".format(delId)

    print(sql1)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()
    cursor1.execute(sql1)
    result = sql_fetch_json(cursor1)
    father = result[0]['father']
    sql3 = "delete from inspirationfenlei where father ='{}'".format(delId)

    try:
        if father == '-1':
            cursor2.execute(sql2)
            cursor3.execute(sql3)
            print(sql2)
            print(sql3)
            db.commit()
        else:
            cursor2.execute(sql2)
            print(sql2)
            db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})

def getInspirationTreeData():
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "select * from inspirationfenlei"
    cursor.execute(sql)
    items = sql_fetch_json(cursor)
    treeData = []
    for item in items:
        father = item['father']
        if father == "-1":
            data = []
            father_ = item['value']
            for item_ in items:
                if item_['father'] == father_:
                    data.append(item_)
            item["data"] = data
            treeData.append(item)
    return treeData

##面料收藏
@app.route('/addInspirationStorage', methods=['POST', 'GET'])
def addInspirationStorage():
    status = request.form.get('storageStatus')
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)

    sql = "select storageNum from inspiration where imageId = '{}'".format(imageId)
    cursor = db.cursor()
    cursor.execute(sql)
    storageNums = sql_fetch_json(cursor)
    storageNum = int(storageNums[0]["storageNum"])

    if status =="1":
        try:
            cursor1 = db.cursor()
            sql1 = "select * from inspiration where imageId = '{}'".format(imageId)
            print(sql1)
            cursor1.execute(sql1)
            graphics = sql_fetch_json(cursor1)
            graphic = graphics[0]
            storageId = username + imageId
            sql2 = "INSERT INTO  inspirationstorage (username,imageId, imageUrl, title, type, provider, creatDate,storageId ) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')".format(
                                            username, imageId,graphic['imageUrl'],
                                           graphic['title'],graphic['type'],
                                           graphic['provider'],graphic['creatDate'], storageId)
            print(sql2)
            cursor2 = db.cursor()
            cursor2.execute(sql2)

            storageNum = storageNum + 1
            sql2_ = "update  inspiration set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor2_ = db.cursor()
            cursor2_.execute(sql2_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '收藏成功!'})
        except Exception:
            return jsonify({'status': '0', 'msg': '该数据已收藏!'})
    if status =="0":
        try:
            cursor3 = db.cursor()
            sql3 = "delete from inspirationstorage where imageId ='{}'".format(imageId)
            cursor3.execute(sql3)

            storageNum = storageNum - 1
            sql3_ = "update  inspiration set storageNum = {} WHERE imageId ='{}'".format(storageNum, imageId)
            cursor3_ = db.cursor()
            cursor3_.execute(sql3_)
            db.commit()
            db.close()
            return jsonify({'status': '1', 'msg': '取消收藏!'})
        except Exception:

            return jsonify({'status': '0', 'msg': '取消收藏失败!'})

@app.route('/getMySorageInspirationById', methods=['POST', 'GET'])
def getMySorageInspirationById():
    username = request.form.get('username')
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "select * from inspirationstorage where username='{}' and imageId ='{}'".format(username,imageId)
        print(sql)
        count = cursor.execute(sql)
        db.commit()
        db.close()
        if count >0:
            return jsonify({'status': '1'})
        else:
            return jsonify({'status': '0'})
    except Exception:

        return jsonify({'status': '0'})

@app.route('/inspirationStorageManage')
def inspirationStorageManage():
    return render_template("inspiration/inspirationStorageManage.html")
@app.route('/inspirationStorageManageList', methods=['POST', 'GET'])
def inspirationStorageManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from inspirationstorage where username = '{}' limit {}, {} ".format(username, start, size)
        sql2 = "select * from inspirationstorage where username = '{}'".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from inspirationstorage where username = '{}' and type like '{}' limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from inspirationstorage where username = '{}' and type like '{}' ".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#系统款式细节管理
@app.route('/sysInspirationManage')
def sysInspirationManage():
    return render_template("inspiration/inspirationManage.html")

@app.route('/inspirationManageList', methods=['POST', 'GET'])
def inspirationManageList():
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from inspiration order by creatDate desc limit {}, {} ".format(start, size)
        sql2 = "select * from inspiration order by creatDate desc"
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from inspiration where type like '{}' order by creatDate desc limit {}, {} ".format(query, start, size)
        sql2 = "select * from inspiration where type like '{}' order by creatDate desc ".format(query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
#我的款式手稿
@app.route('/myInspirationManageList', methods=['POST', 'GET'])
def myInspirationManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from inspiration where provider = '{}' order by creatDate desc limit {}, {} ".format(username, start, size)
        sql2 = "select * from inspiration where provider = '{}' order by creatDate desc".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from inspiration where provider = '{}' and type like '{}' order by creatDate desc limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from inspiration where provider = '{}' and type like '{}' order by creatDate desc".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/myInspirationManage')
def myInspirationManage():
    return render_template("inspiration/myInspirationManage.html")

@app.route('/addInspiration')
def addInspiration():
    treeData = getInspirationTreeData()
    return render_template("inspiration/addInspiration.html", treeData=treeData)
@app.route('/saveMyInspiration', methods=['POST', 'GET'])
def saveMyInspiration():
    imageName = request.form.get('imageName')
    type = request.form.get('type')
    title = request.form.get('title')
    imageUrl = request.form.get('imageUrl')
    imageId = request.form.get('imageId')
    creatDate = datetime.now()
    provider = current_user.username
    status = 0
    storageNum = 0
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "INSERT INTO  inspiration (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{})".format(
            imageName, type,title,imageUrl,imageId,provider,creatDate, status,storageNum)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '该数据已存在!'})
@app.route('/index')
def index():
    return render_template("index.html")

#以图收图
@app.route('/searchImage')
@login_required
def searchImage():
    return render_template("./search/searchImage.html")
from utils.spiderByImage import getImagByImage
@app.route('/searchImageByImage', methods=['POST', 'GET'])
def searchImageByImage():
    imgUrl = request.form.get("imageUrl")
    maxWaitTime = request.form.get("maxWaitTime")
    try:
        getImg = getImagByImage(maxWaitTime)
        imgs = getImg.getData(imgUrl)
        return  jsonify({'status': 1, 'msg': '搜集数据结束','data':imgs})
    except Exception:
        return jsonify({'status': 0, 'msg': '搜集数据失败'})
@app.route('/searchList', methods=['POST', 'GET'])
def searchList():
    return render_template("./search/searchList.html")

@app.route('/toStorageImage', methods=['POST', 'GET'])
def toStorageImage():
    img_url = request.args.get("img_url")
    if img_url!=None and img_url!="":
        _url = json.loads(img_url)
    else:
        _url = {"img_url":""}
    return render_template("./search/toStorageImage.html", img_url= _url["img_url"])

@app.route('/getFenleiTree', methods=['POST', 'GET'])
def getFenleiTree():
    bigClass = request.form.get("bigClass")
    treeData = None
    if bigClass == "0":
        treeData = getGraphicsTreeData()
    if bigClass == "1":
        treeData = getStylesTreeData()
    if bigClass == "2":
        treeData = getDetailsTreeData()
    if bigClass == "3":
        treeData = getFabricsTreeData()
    if bigClass == "4":
        treeData = getAccessoriesTreeData()
    if bigClass == "5":
        treeData = getInspirationTreeData()
    return  jsonify({'status': 1,'treeData':treeData})
import hashlib
@app.route('/saveStorageImage', methods=['POST', 'GET'])
def saveStorageImage():
    imageName = request.form.get('imageName')
    type = request.form.get('type')
    title = request.form.get('title')
    imageUrl = request.form.get('imageUrl')
    provider = current_user.username
    imageId_ = str(imageUrl+provider)
    imageId = hashlib.md5(imageId_.encode(encoding='UTF-8')).hexdigest()
    creatDate = datetime.now()
    status = 0
    storageNum = 0
    lib = int(request.form.get("lib"))
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "INSERT INTO  imagestorage (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum,lib) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{},{})".format(
            imageName, type,title,imageUrl,imageId,provider,creatDate, status,storageNum, lib)
        print(sql)
        cursor.execute(sql)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '保存成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '该数据已存在!'})

@app.route('/myImageManage', methods=['POST', 'GET'])
def myImageManage():
    return render_template("./search/imageStorageList.html")

@app.route('/imageManageList', methods=['POST', 'GET'])
def imageManageList():
    username = current_user.username
    page = int(request.args.get("page"))
    size = int(request.args.get("limit"))
    query = request.args.get("q")
    start = (page - 1) * size
    db = pymysql.connect(**config)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    if query == None or query == "":
        sql1 = "select * from imagestorage where provider = '{}' order by creatDate desc limit {}, {} ".format(username, start, size)
        sql2 = "select * from imagestorage where provider = '{}' order by creatDate desc".format(username)
        print(sql1)
        print(sql2)
    else:
        sql1 = "select * from imagestorage where provider = '{}' and type like '{}' order by creatDate desc limit {}, {} ".format(username, query, start, size)
        sql2 = "select * from imagestorage where provider = '{}' and type like '{}' order by creatDate desc".format(username, query)
        print(sql1)
        print(sql2)
    cursor1.execute(sql1)
    count = cursor2.execute(sql2)
    resultlist = sql_fetch_json(cursor1)
    results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
    db.commit()
    db.close()
    return jsonify(results)
@app.route('/updateImageStorageStaus', methods=['POST', 'GET'])
def updateImageStorageStaus():
    status = int(request.form.get('status'))
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        cursor = db.cursor()
        sql = "update imagestorage set status={} where imageId ='{}'".format(int(status),imageId)
        print(sql)
        cursor.execute(sql)
        sql1 = "select * from imagestorage where imageId = '{}'".format(imageId)
        print(sql1)
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        images = sql_fetch_json(cursor1)
        print(images)
        image = images[0]
        lib = image["lib"]
        lib_ = ""
        if lib == 0:
            lib_ = "graphics"
        if lib == 1:
            lib_ = "styles"
        if lib == 2:
            lib_ = "details"
        if lib == 3:
            lib_ = "fabrics"
        if lib == 4:
            lib_ = "accessories"
        if lib == 5:
            lib_ = "inspiration"
        print(lib_, status)
        msg = ""
        if status==1:
            sql2 = "INSERT INTO  {} (imageName,type, title, imageUrl, imageId, provider, creatDate,status ,storageNum) " \
              "VALUES ('{}','{}','{}','{}','{}','{}','{}',{},{})".format(lib_,image["imageName"], image["type"],image["title"],image["imageUrl"],image["imageId"],image["provider"],image["creatDate"], 0,0)
            print(sql2)
            cursor2 = db.cursor()
            cursor2.execute(sql2)
            msg = "图像已收纳进库"
        else:
            sql3 = "delete from {} WHERE imageId = '{}'".format(lib_, imageId)
            print(sql3)
            cursor3 = db.cursor()
            cursor3.execute(sql3)
            msg = "图像已从库中移出"
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': msg})
    except Exception:
        return jsonify({'status': '0', 'msg': '操作失败!'})
@app.route('/deleteImageStorage', methods=['POST', 'GET'])
def deleteImageStorage():
    imageId = request.form.get('imageId')
    db = pymysql.connect(**config)
    try:
        sql1 = "select * from imagestorage where imageId = '{}'".format(imageId)
        print(sql1)
        cursor1 = db.cursor()
        cursor1.execute(sql1)
        images = sql_fetch_json(cursor1)
        image = images[0]
        lib = image["lib"]
        lib_ = ""
        if lib == 0:
            lib_ = "graphics"
        if lib == 1:
            lib_ = "styles"
        if lib == 2:
            lib_ = "details"
        if lib == 3:
            lib_ = "fabrics"
        if lib == 4:
            lib_ = "accessories"
        if lib == 5:
            lib_ = "inspiration"
        cursor2 = db.cursor()
        sql2 = "delete from imagestorage WHERE imageId = '{}'",format(imageId)
        print(sql2)
        cursor2.execute(sql2)
        cursor3 = db.cursor()
        sql3 = "delete from {} WHERE imageId = '{}'", format(lib_, imageId)
        print(sql3)
        cursor3.execute(sql3)
        db.commit()
        db.close()
        return jsonify({'status': '1', 'msg': '删除成功!'})
    except Exception:
        return jsonify({'status': '0', 'msg': '删除失败!'})

@app.route('/searchImageByThisImage', methods=['POST', 'GET'])
def searchImageByThisImage():
    img_url = request.args.get("imageUrl")
    print(img_url)
    if img_url != None and img_url != "":
        _url = json.loads(img_url)
    else:
        _url = {"img_url": ""}
    maxWaitTime = 10
    try:
        getImg = getImagByImage(maxWaitTime)
        imgs = getImg.getData(_url["img_url"])
        return  render_template("./search/searchList.html", imgs = imgs)
    except Exception:
        return jsonify({'status': 0, 'msg': '搜集数据失败'})
@app.route('/admin', methods=['POST', 'GET'])
def admin():
    graphics = tongjiWeek("graphics")
    fabrics= tongjiWeek("fabrics")
    details= tongjiWeek("details")
    accessories= tongjiWeek("accessories")
    inspiration= tongjiWeek("inspiration")
    styles= tongjiWeek("styles")
    lables = graphics["lables"]
    totalnums = np.array(graphics["nums"])+np.array(fabrics["nums"])\
                +np.array(details["nums"])+np.array(accessories["nums"])\
                +np.array(inspiration["nums"])+np.array(styles["nums"])
    totalnums_ = totalnums.tolist()
    allDataWeek = {"lables":lables, "totalnums":totalnums_,"graphics":graphics["nums"],
                   "fabrics":fabrics["nums"], "details":details["nums"],"accessories":accessories["nums"],
                   "inspiration": inspiration["nums"],"styles":styles["nums"],}

    zhanbiData = tongjiZhanbi();

    storageData = tongjiStorage();


    return render_template("./admin.html", allDataWeek= allDataWeek, zhanbiData= zhanbiData, storageData= storageData)


def tongjiWeek(table):
    db = pymysql.connect(**config)
    cursor = db.cursor()
    sql = "SELECT * FROM {} WHERE DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(creatDate); ".format(table)
    print(sql)
    cursor.execute(sql)
    results = sql_fetch_json(cursor)
    Dates = []
    if len(results) >0:
        for result in results:
            Dates.append(result["creatDate"].strftime("%Y-%m-%d"))
    lables = []
    nums = []
    for i in range(7):
        date = DT.datetime.now() - DT.timedelta(days=i)
        lables.append(date.strftime("%Y-%m-%d"))
        if len(results) > 0:
            nums.append(float(sum(np.array(Dates) == date.strftime("%Y-%m-%d"))))
        else:
            nums.append(float(0))
    return {"lables":lables[::-1], "nums":nums[::-1]}
def tongjiZhanbi():
    tables= ["graphics","fabrics","details","accessories","inspiration","styles"]
    lables = ["图案","面料","款式细节","服饰品","灵感源","款式手稿"]
    nums = []
    db = pymysql.connect(**config)
    for i in range(len(tables)):
        cursor = db.cursor()
        sql = "select * from {}".format(tables[i])
        count = cursor.execute(sql)
        data = {"value":float(count),"name":lables[i]}
        nums.append(data)
    db.commit()
    db.close()
    return {"lables": lables, "nums": nums}
def tongjiStorage():
    db = pymysql.connect(**config)
    tables = ["graphics", "fabrics", "details", "accessories", "inspiration", "styles"]
    times = []
    for i in range(7):
        date = DT.datetime.now() - DT.timedelta(days=i)
        times.append(date.strftime("%Y-%m-%d"))
    result = {}
    for table in tables:
        dlist = []
        for d in times:
            sql="SELECT SUM(storageNum) FROM {} WHERE creatDate = '{}'".format(table,d)
            cursor = db.cursor()
            cursor.execute(sql)
            count = cursor.fetchall()[0][0]
            if count ==None:
                dlist.append(float(0))
            else:
                dlist.append(float(count))
        result[table]=dlist[::-1]
    return {"lables": times[::-1], "nums": result}
@app.route('/tongji', methods=['POST', 'GET'])
def tongji():
    table = request.args.get("table")
    result = tongjiWeek(table)
    lables = result["lables"]
    allDataWeek = {"lables":lables, "newAddNum":result["nums"]}
    totalData = tongjiTotal(table)
    classData = tongjiClass(table)
    myStorage = tongjiMyStorage(table)

    return render_template("./tongji.html", allDataWeek= allDataWeek,totalData=totalData, classData= classData, myStorage=myStorage)

def tongjiTotal(table):
    db = pymysql.connect(**config)
    times = []
    for i in range(7):
        date = DT.datetime.now() - DT.timedelta(days=i)
        times.append(date.strftime("%Y-%m-%d"))
    nums = []
    for time in times:
        sql = "select * from {} WHERE creatDate <= '{}'".format(table, time)
        cursor = db.cursor()
        count = cursor.execute(sql)
        nums.append(float(count))
    return {"lables": times[::-1], "nums": nums[::-1]}
def tongjiClass(table):
    db = pymysql.connect(**config)
    fenleitable = table+"fenlei"
    sql1 = "SELECT title FROM {} WHERE father != {}".format(fenleitable, -1)
    cursor1 = db.cursor()
    cursor1.execute(sql1)
    types= sql_fetch_json(cursor1)
    TYPES = []
    NUMS = []
    for type in types:
        sql = "select * from {} WHERE  type = '{}'".format(table, type["title"])
        cursor = db.cursor()
        count = cursor.execute(sql)
        TYPES.append(type["title"])
        NUMS.append(float(count))
    # print(TYPES)
    # print(NUMS)
    datas = []
    if len(TYPES)>10:
        numarrys = np.array(NUMS)
        index = numarrys.argsort()
        numarrys_ = np.sort(numarrys)
        nums = numarrys_[numarrys_.shape[0] - 10:]
        index_ = index[index.shape[0]-10:]
        TYPES_ = []
        for i in index_:
            TYPES_.append(TYPES[i])
        for j in range(len(TYPES_)):
            datas.append({"name":TYPES_[j],"value":nums[j]})
        return {"lables":TYPES_, "nums":datas}
    else:
        for k in range(len(TYPES)):
            datas.append({"name": TYPES[k], "value": NUMS[k]})
        return {"lables":TYPES, "nums":datas}
def tongjiMyStorage(table):
    db = pymysql.connect(**config)
    fenleitable = table+"fenlei"
    sql1 = "SELECT title FROM {} WHERE father != {}".format(fenleitable, -1)
    cursor1 = db.cursor()
    cursor1.execute(sql1)
    types= sql_fetch_json(cursor1)
    TYPES = []
    NUMS = []
    for type in types:
        sql = "select * from {} WHERE  type = '{}'".format(table+"storage", type["title"])
        cursor = db.cursor()
        count = cursor.execute(sql)
        TYPES.append(type["title"])
        NUMS.append(float(count))
    # print(TYPES)
    # print(NUMS)
    datas = []
    if len(TYPES)>10:
        numarrys = np.array(NUMS)
        index = numarrys.argsort()
        numarrys_ = np.sort(numarrys)
        nums = numarrys_[numarrys_.shape[0] - 10:]
        index_ = index[index.shape[0]-10:]
        TYPES_ = []
        for i in index_:
            TYPES_.append(TYPES[i])
        for j in range(len(TYPES_)):
            datas.append({"name":TYPES_[j],"value":nums[j]})
        return {"lables":TYPES_, "nums":datas}
    else:
        for k in range(len(TYPES)):
            datas.append({"name": TYPES[k], "value": NUMS[k]})
        return {"lables":TYPES, "nums":datas}
@app.template_filter('datetime_format')
def _jinja2_filter_datetime_format(datetimeValue, format="%Y-%m-%d"):
    return datetimeValue.strftime(format)
if __name__ == '__main__':
    app.run(host='192.168.3.2',port=8080)
