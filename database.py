__author__ = 'Jungsik Choi'

from sqlite3 import dbapi2 as sqlite3
from flask import _app_ctx_stack


class Database():

    def __init__(self, _app, _db_path):
        self.db_path = _db_path
        self.app = _app

        """Initializes the database."""
        with self.app.app_context():
            db = self.get_db()
            with self.app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()


    def get_db(self):
        """
        Opens a new database connection if there is none yet for the
        current application context.
        """
        top = _app_ctx_stack.top
        if not hasattr(top, 'sqlite_db'):
            top.sqlite_db = sqlite3.connect(self.db_path)
        return top.sqlite_db
        
                
    def close_connection(self):
        """Closes the database again at the end of the request."""
        top = _app_ctx_stack.top
        if hasattr(top, 'sqlite_db'):
            top.sqlite_db.close()


    def query_db(self, query, args=(), one=False):
        db = self.get_db()
        cur = db.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv


    def insert_entry(self, _id, _time):
        query = 'insert into entries (user_id, elapsed_time) '
        query += 'values ("' + _id + '", ' + str(_time) + ')'
        print '  DB>> ' + query
        try:
            db = self.get_db()
            db.execute(query)
            db.commit()
        except Exception as inst:
            print type(inst)
            return False
        else:
            return True


    def get_id_list(self):
        query = 'select user_id from entries'
        print '  DB>> ' + query
        db = self.get_db()
        cur = db.execute(query)
        id_list = cur.fetchall()
        return id_list


    def get_entries(self):
        db = self.get_db()
        query = 'select user_id, elapsed_time from entries order by elapsed_time limit 10'
        print '  DB>> ' + query
        cur = db.execute(query)
        entries = [dict(user_id=row[0], elapsed_time=row[1]) for row in cur.fetchall()]
        return entries

