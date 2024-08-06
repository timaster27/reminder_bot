from psycopg import connect, errors, sql

from settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS


def create_database():
    conn = connect(user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    conn.autocommit = True
    try:
        create_cmd = sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DB_NAME))
        cur.execute(create_cmd)
        conn.close()
    except errors.DuplicateDatabase:
        conn.rollback()
    conn = connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    try:
        cur.execute('''CREATE TABLE REMINDER
              (CHAT_ID BIGINT NOT NULL,
              MSG_ID VARCHAR NOT NULL,
              MESSAGE VARCHAR,
              START_DATE TIMESTAMP,
              END_DATE TIMESTAMP,
              REPEAT VARCHAR(20),
              PRIMARY KEY (CHAT_ID, MSG_ID)
              );''')
        conn.commit()
    except errors.DuplicateTable:
        conn.rollback()
    try:
        cur.execute('''CREATE TABLE WHITELIST
              (USER_ID BIGINT NOT NULL PRIMARY KEY
              );''')
        conn.commit()
    except errors.DuplicateTable:
        conn.rollback()
    return conn, cur


conn, cur = create_database()


def add(chat_id, msg_id, message, start, end, repeat):
    try:
        cur.execute("INSERT INTO REMINDER VALUES (%s, %s, %s, %s, %s, %s)",
                    [chat_id, msg_id, message, start, end, repeat])
    except errors.UniqueViolation:
        conn.rollback()
    conn.commit()


def delete_reminder(chat_id, msg_id):
    cur.execute("DELETE FROM REMINDER WHERE CHAT_ID=(%s) AND MSG_ID=(%s)", [chat_id, msg_id])
    conn.commit()


def select_reminder(chat_id=None):
    if chat_id:
        cur.execute("SELECT * FROM REMINDER WHERE CHAT_ID=(%s);", [chat_id])
    else:
        cur.execute("SELECT * FROM REMINDER;")
    return cur.fetchall()


def add_user(user_id):
    try:
        cur.execute("INSERT INTO WHITELIST VALUES (%s)", [user_id])
    except errors.UniqueViolation:
        conn.rollback()
    conn.commit()


def delete_user(user_id):
    cur.execute("DELETE FROM WHITELIST WHERE USER_ID=(%s)", [user_id])
    conn.commit()


def select_user():
    cur.execute("SELECT * FROM WHITELIST;")
    return cur.fetchall()
