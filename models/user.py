from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import UserMixin
import json
from flask import Flask, render_template, request, json, jsonify, Response
import uuid
import pymysql
config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'app-design',
        'charset': 'utf8',
        'cursorclass': pymysql.cursors.Cursor,
    }
class User(UserMixin):
    def __init__(self, username):
        self.username = username
        self.id = self.get_id()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        db = pymysql.connect(**config)
        cursor1 = db.cursor()
        try:
            sql = "INSERT INTO  user (username ,password, userId )VALUES ('{}','{}','{}')".format(self.username, self.password_hash, self.id)
            print(sql)
            cursor1.execute(sql)
            db.commit()
            db.close()
        except Exception:
            print("注册失败")

    def verify_password(self, password):
        db = pymysql.connect(**config)
        if self.username is not None:
            cursor = db.cursor()
            sql = "select password from user WHERE username ='{}'".format(self.username)
            print(sql)
            count  = cursor.execute(sql)
            if count == 0:
                return False
            else:
                result = sql_fetch_json(cursor)
                self.password_hash = result[0]["password"];
                return check_password_hash(self.password_hash, password)
        else:
            return False

    def get_id(self):
        """get user id from profile file, if not exist, it will
        generate a uuid for the user.
        """
        db = pymysql.connect(**config)
        if self.username is not None:

            cursor2 = db.cursor()
            sql = "select userId from user WHERE username ='{}'".format(self.username)
            print(sql)
            count  = cursor2.execute(sql)

            if count == 0:
                return uuid.uuid4()
            else:
                result = sql_fetch_json(cursor2)
                return result[0]["userId"];

        db.commit()
        db.close()
        return uuid.uuid4()

    @staticmethod
    def get(user_id):
        """try to return user_id corresponding User object.
        This method is used by load_user callback function
        """
        db = pymysql.connect(**config)
        if not user_id:
            return None
        try:
            cursor3 = db.cursor()
            sql = "select * from user WHERE userId ='{}'".format(user_id)
            print(sql)
            count = cursor3.execute(sql)
            if count == 0:
                return None
            else:
                result = sql_fetch_json(cursor3)
                username = result[0]['username']
                return User(username)
        except:
            return None
        return None
    def userList(self, page, size, query):
        start = (page - 1) * size
        db = pymysql.connect(**config)
        cursor1 = db.cursor()
        cursor2 = db.cursor()
        if query == None or query == "":
            sql1 = "select * from user limit {}, {} ".format(start, size)
            sql2 = "select * from user "
            print(sql1)
            print(sql2)
        else:
            sql1 = "select * from user where username like '{}' limit {}, {} ".format(query,start,size)
            sql2 = "select * from user where username like '{}' ".format(query)
            print(sql1)
            print(sql2)
        cursor1.execute(sql1)
        count = cursor2.execute(sql2)
        resultlist = sql_fetch_json(cursor1)
        results = {"data": resultlist, "count": count, "code": 0, "msg": ""}
        db.commit()
        db.close()
        return jsonify(results)
    def findByUserId(self, userId):
        db = pymysql.connect(**config)
        cursor = db.cursor()
        sql = "select * from user where userId = '{}'".format(userId)
        print(sql)
        cursor.execute(sql)
        results = sql_fetch_json(cursor)
        db.commit()
        db.close()
        return results[0]
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



