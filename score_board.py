__author__ = 'Jungsik Choi'

from flask import Flask, request, redirect, \
         url_for, render_template, flash, _app_ctx_stack
from werkzeug import secure_filename
from sqlite3 import dbapi2 as sqlite3
import os
import subprocess
import re
from database import Database
#from tester_thread import ProgramTester


# Configuration
UPLOAD_FOLDER = 'source_code'
ALLOWED_EXTENSIONS = set(['c', 'h'])
VERIFY_N = 13
EXAMPLE_PATH = 'example-11.out'
DATABASE = 'score_board.db'
ADDRESS = '115.145.179.127'
DANGEROUS_FUNCS = set(['exec', 'execl', 'execlp', 'execle', 'execv',
        'execve', 'execvp', 'execvpe', 'system', 'accept', 'connect',
        'socket', 'unlink', 'remove'])


# Create our application
app = Flask(__name__)


# Create classes
db = Database(DATABASE)
#tester = ProgramTester(db, UPLOAD_FOLDER, VERIFY_N, EXAMPLE_PATH)


"""
@app.teardown_appcontext
def close_connection(exception):
    db.close_connection()
"""


def execute(_cmd):
    print ' EXE>> ' + _cmd
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


@app.route('/CompileSource/<user_id>')
def compile_source(user_id):
    print '/CompileSource/' + user_id
    directory = UPLOAD_FOLDER + '/' + user_id

    file_list = None

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

    # Push this program to job queue
    msg = user_id + '!! Your program has been registered.\n'
    msg += 'Please check your score after a while.'
    flash(msg)

    """
    if not tester.running:
        tester.start()
    """

    return redirect(url_for('show_entries'))


@app.route('/UploadSource/<user_id>', methods=['GET', 'POST'])
def upload_source(user_id):
    print '/UploadSource/' + user_id
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


@app.route('/Login', methods=['GET', 'POST'])
def login():
    print '/Login'
    error = None

    if request.method == 'POST':
        user_id = request.form['username']

        if user_id == '':
            error = 'Enter a string!!'
            return render_template('login.html', error=error)

        expression = '\W'
        re_compile = re.compile(expression)
        re_search = re_compile.search(user_id)

        if re_search:
            error = 'You can enter alphabets and numbers[a-zA-Z0-9]'
            return render_template('login.html', error=error)

        # Dir Check
        directory = 'source_code/' + user_id
        if os.path.exists(directory):
            print 'LOGIN>This dir is existing : ' + directory
            error = user_id + ' is already in use. Type a different ID'
            return render_template('login.html', error=error)

        # DB Check
        existing_id_list = db.get_id_list()

        for existing_id in existing_id_list:
            if user_id == existing_id[0]:
                error = user_id + ' is already in use. Type a different ID'
                return render_template('login.html', error=error)

        existing_id_list = db.get_id_list_from_err()

        for existing_id in existing_id_list:
            if user_id == existing_id[0]:
                error = user_id + ' is already in use. Type a different ID'
                return render_template('login.html', error=error)

        return redirect(url_for('upload_source', user_id = user_id))
    return render_template('login.html', error=error)


@app.route('/FullList')
def show_full_entries():
    print '/FullList'
    entries = db.get_full_entries()
    error_logs = db.get_error_logs()
    return render_template('show_full_entries.html', 
            entries=entries, error_logs=error_logs)

@app.route('/')
def show_entries():
    print '/'
    entries = db.get_entries()
    return render_template('show_entries.html', entries=entries)


if __name__ == '__main__':
    app.debug = True
    app.secret_key='development key'
    app.run(host=ADDRESS, port=8080)
    #tester.run()

