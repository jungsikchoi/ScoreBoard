from flask import Flask, request, redirect, url_for, render_template, g, flash
from flask import send_from_directory, _app_ctx_stack
from werkzeug import secure_filename
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
import os
import subprocess
import re

# Configuration
UPLOAD_FOLDER = 'source_code'
ALLOWED_EXTENSIONS = set(['c', 'h'])
DATABASE='score_board.db'

# Create our application
app = Flask(__name__)

# Global variable
req_cnt = 0


def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(DATABASE)
    return top.sqlite_db


@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute(_cmd):
    fd = subprocess.Popen(_cmd, shell=True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
    return fd.stdout, fd.stderr

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/Test', methods=['GET', 'POST'])
def upload_source():
    global req_cnt
    req_cnt = req_cnt + 1

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return redirect(url_for('test_source',
                        filename=filename))
        else:
            flash('You can upload only .c file.')
    return render_template('upload_code.html')

@app.route('/TestSource/<filename>')
def test_source(filename):
    global req_cnt
    cmd = 'gcc ' + UPLOAD_FOLDER + '/*.c -o ' + UPLOAD_FOLDER + '/nqueens'
    std_out, std_err = execute(cmd)

    result = 'NULL'

    for line in std_err.readlines() :
        if line.find('error') > 0:
            flash('Compile Error!!')
            cmd = 'rm -rf ' + UPLOAD_FOLDER + '/*'
            print cmd
            std_out, std_err = execute(cmd)
            return redirect(url_for('show_entries'))

    cmd = 'time ' + UPLOAD_FOLDER + '/nqueens'
    print cmd

    std_out, std_err = execute(cmd)

    for line in std_err.readlines() :
        try:
            re_compile = re.compile(r'^\d+\.\d+user\s+\d+\.\d+system\s+(?P<minute>\d+):(?P<second>\d+\.\d+)elapsed\s')
            re_match = re_compile.match(line)
            minute = float(re_match.group('minute'))
            second = float(re_match.group('second'))
            elapsed_time = minute * 60 + second
            result = str(elapsed_time)
        except:
            pass

    cmd = 'rm -rf ' + UPLOAD_FOLDER + '/*'
    print cmd
    std_out, std_err = execute(cmd)

    user_id = get_user_id()

    return add_entry(user_id, elapsed_time)

def get_user_id():
    query = 'select max(user_id) from entries'
    print query
    db = get_db()
    cur = db.execute(query)
    max_id = cur.fetchall()
    try:
        user_id = int((max_id[0])[0]) + 1
    except TypeError:
        user_id = 1
    return user_id

def add_entry(_id, _time):
    query = 'insert into entries (user_id, elapsed_time) '
    query += 'values (' + str(_id) + ', ' + str(_time) + ')'
    print query
    db = get_db()
    db.execute(query)
    db.commit()
    msg = 'Your ID is #' + str(_id) + '.  '
    msg += 'Elapsed Time is ' + str(_time) + 'sec'
    flash(msg)
    return redirect(url_for('show_entries'))

@app.route('/')
def show_entries():
    db = get_db()
    query = 'select user_id, elapsed_time from entries order by elapsed_time limit 10'
    print query
    cur = db.execute(query)
    entries = [dict(user_id=row[0], elapsed_time=row[1]) for row in cur.fetchall()]

    print entries
    
    return render_template('show_entries.html', entries=entries)

if __name__ == '__main__':
    init_db()
    app.debug = True
    app.secret_key='development key'
    app.run(host='115.145.178.206')
