__author__ = 'Jungsik Choi'

from flask import Flask, request, redirect, \
         url_for, render_template, flash, _app_ctx_stack
from werkzeug import secure_filename
from sqlite3 import dbapi2 as sqlite3
import os
import subprocess
import re
from database import Database


# Configuration
UPLOAD_FOLDER = 'source_code'
ALLOWED_EXTENSIONS = set(['c', 'h'])
DATABASE = 'score_board.db'
ADDRESS = '115.145.178.206'
DANGEROUS_FUNCS = set(['exec', 'execl', 'execlp', 'execle', 'execv',
        'execve', 'execvp', 'execvpe', 'system'])



# Create our application
app = Flask(__name__)


# Create classes
db = Database(app, DATABASE)


@app.teardown_appcontext
def close_connection(exception):
    db.close_connection()


def execute(_cmd):
    print ' EXE>> '
    fd = subprocess.Popen(_cmd, shell=True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
    return fd.stdout, fd.stderr


def delete_dir(_directory):
    cmd = 'rm -rf ' + _directory
    std_out, std_err = execute(cmd)
    

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def add_entry(_id, _time):
    if (db.insert_entry(_id, _time)):
        msg = _id + '!!  '
        msg += 'Your elapsed time is ' + str(_time) + 'sec'
    else:
        msg = 'DB Error'
    flash(msg)
    return redirect(url_for('show_entries'))


@app.route('/TestSource/<user_id>')
def test_source(user_id):
    directory = UPLOAD_FOLDER + '/' + user_id

    # Security test
    for root, dirs, file_list in os.walk(directory):
        pass

    for file_name in file_list:
        file_path = directory + '/' + file_name
        test_file = open(file_path, 'r')
        lines = test_file.readlines()
        for line in lines:
            for func_name in DANGEROUS_FUNCS:
                expression = '\s*' + func_name +'\s*\('
                re_compile = re.compile(expression)
                re_search = re_compile.search(line)
                if re_search:
                    print ' >> dangerous func is founded!!' 
                    print ' >> ' + line
                    flash('Dangerous code has been found')
                    delete_dir(directory)
                    return redirect(url_for('show_entries'))
    
    # Copile
    cmd = 'gcc ' + directory + '/*.c '
    cmd += '-o ' + directory + '/nqueens'
    std_out, std_err = execute(cmd)
    result = 'NULL'

    for line in std_err.readlines() :
        if line.find('error') > 0:
            flash('Compile Error!!')
            delete_dir(directory)
            return redirect(url_for('show_entries'))

    # Measure the elapsed time
    cmd = 'time ' + directory + '/nqueens'
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

    # Delete files the test has been completed 
    delete_dir(directory)

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

        existing_id_list = db.get_id_list()

        for existing_id in existing_id_list:
            if user_id == existing_id[0]:
                error = user_id + ' is already in use. Type a different ID'
                return render_template('login.html', error=error)

        return redirect(url_for('upload_source', user_id = user_id))
    return render_template('login.html', error=error)


@app.route('/')
def show_entries():
    entries = db.get_entries()
    return render_template('show_entries.html', entries=entries)


if __name__ == '__main__':
    app.debug = True
    app.secret_key='development key'
    app.run(host=ADDRESS, port=8080)
