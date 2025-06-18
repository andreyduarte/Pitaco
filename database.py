import sqlite3
from flask import current_app, g
import json

DATABASE = 'notifications.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with current_app.app_context():
        db = get_db()
        with current_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def close_db(error=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_notification(content, embedding):
    db = get_db()
    db.execute('INSERT INTO notifications (content, embedding) VALUES (?, ?)',
               (content, json.dumps(embedding)))
    db.commit()
