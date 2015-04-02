__author__ = 'Jungsik Choi'

from flask import Flask, request, redirect, \
         url_for, render_template, flash, _app_ctx_stack
from werkzeug import secure_filename
from sqlite3 import dbapi2 as sqlite3
import os
import subprocess
import re


# Configuration
UPLOAD_FOLDER = 'source_code'
ALLOWED_EXTENSIONS = set(['c', 'h'])
DATABASE = 'score_board.db'
ADDRESS = '115.145.178.206'


# Create our application
app = Flask(__name__)


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


def add_entry(_id, _time):
    query = 'insert into entries (user_id, elapsed_time) '
    query += 'values ("' + _id + '", ' + str(_time) + ')'
    print ' >> ' + query
    db = get_db()
    db.execute(query)
    db.commit()
    msg = _id + '!!  '
    msg += 'Your elapsed time is ' + str(_time) + 'sec'
    flash(msg)
    return redirect(url_for('show_entries'))


@app.route('/TestSource/<user_id>')
def test_source(user_id):
    directory = UPLOAD_FOLDER + '/' + user_id
    cmd = 'gcc ' + directory + '/*.c '
    cmd += '-o ' + directory + '/nqueens'
    std_out, std_err = execute(cmd)
    result = 'NULL'

    for line in std_err.readlines() :
        if line.find('error') > 0:
            flash('Compile Error!!')
            cmd = 'rm -rf ' + directory + '/*'
            print ' >> ' + cmd
            std_out, std_err = execute(cmd)
            return redirect(url_for('show_entries'))

    cmd = 'time ' + directory + '/nqueens'
    print ' >> ' + cmd
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

    '''
    cmd = 'rm -rf ' + directory + '/*'
    print ' >> ' + cmd
    std_out, std_err = execute(cmd)
    '''
    return add_entry(user_id, elapsed_time)


@app.route('/UploadSource/<user_id>', methods=['GET', 'POST'])
def upload_source(user_id):
    directory = UPLOAD_FOLDER + '/' + user_id + '/'

    if not os.path.exists(directory):
        os.makedirs(directory)

    for root, dirs, file_list in os.walk(directory):
        pass

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(directory, filename))
            for root, dirs, file_list in os.walk(directory):
                pass
        else:
            flash('You can upload only .c and .h files.')
    return render_template('upload_source.html', file_list=file_list, user_id=user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        user_id = request.form['username']

        if user_id == '':
            error = 'Enter a string!!'
            return render_template('login.html', error=error)

        query = 'select user_id from entries'
        print ' >> ' + query
        db = get_db()
        cur = db.execute(query)
        existing_id_list = cur.fetchall()

        for existing_id in existing_id_list:
            if user_id == existing_id[0]:
                error = user_id + ' is already in use. Type a different ID'
                return render_template('login.html', error=error)

        return redirect(url_for('upload_source', user_id = user_id))
    return render_template('login.html', error=error)


@app.route('/')
def show_entries():
    db = get_db()
    query = 'select user_id, elapsed_time from entries order by elapsed_time limit 10'
    print ' >> ' + query
    cur = db.execute(query)
    entries = [dict(user_id=row[0], elapsed_time=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)


if __name__ == '__main__':
    init_db()
    app.debug = True
    app.secret_key='development key'
    app.run(host=ADDRESS, port=80)
