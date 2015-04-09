__author__ = 'Jungsik Choi'

import sqlite3

class Database():

    def __init__(self, _db_path):
        self.db_path = _db_path

        db = sqlite3.connect(self.db_path)

        init_file = open('schema.sql')
        db.cursor().executescript(init_file.read())
        db.commit()
        db.close()


    def get_entries(self):
        query = 'select user_id, elapsed_time '
        query += 'from entries order by elapsed_time limit 10'
        print '  DB>> ' + query

        db = sqlite3.connect(self.db_path)
        cur = db.execute(query)
        entries = [dict(user_id=row[0], elapsed_time=row[1]) for row in cur.fetchall()]
        db.close()
        return entries
    

    def get_full_entries(self):
        query = 'select user_id, elapsed_time '
        query += 'from entries order by elapsed_time'
        print '  DB>> ' + query

        db = sqlite3.connect(self.db_path)
        cur = db.execute(query)
        entries = [dict(user_id=row[0], elapsed_time=row[1]) for row in cur.fetchall()]
        db.close()
        return entries
    

    def get_error_logs(self):
        # select user_id, error_log from error_logs;
        query = 'select user_id, error_log '
        query += 'from error_logs'
        print '  DB>> ' + query

        db = sqlite3.connect(self.db_path)
        cur = db.execute(query)
        entries = [dict(user_id=row[0], error_log=row[1]) for row in cur.fetchall()]
        db.close()
        return entries


    def get_id_list(self):
        query = 'select user_id from entries'
        print '  DB>> ' + query
        db = sqlite3.connect(self.db_path)
        cur = db.execute(query)
        id_list = cur.fetchall()
        db.close()
        return id_list


    def get_id_list_from_err(self):
        query = 'select user_id from error_logs'
        print '  DB>> ' + query
        db = sqlite3.connect(self.db_path)
        cur = db.execute(query)
        id_list = cur.fetchall()
        db.close()
        return id_list
        

    def insert_entry(self, _id, _time):
        query = 'insert into entries (user_id, elapsed_time) '
        query += 'values ("' + _id + '", ' + str(_time) + ')'
        print '  DB>> ' + query

        db = sqlite3.connect(self.db_path)
        db.execute(query)
        db.commit()
        db.close()

