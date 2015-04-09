__author__ = 'Jungsik Choi'

import time
import subprocess
import re
import os
import sqlite3

db_path = 'score_board.db'


def insert_entry(_id, _time):
    query = 'insert into entries (user_id, elapsed_time) '
    query += 'values ("' + _id + '", ' + str(_time) + ')'
    print '  [insert_entry] ' + query

    db = sqlite3.connect(db_path)
    db.execute(query)
    db.commit()
    db.close()


def insert_error_log(_id, _log):
    query = 'insert into error_logs (user_id, error_log) '
    query += 'values ("' + _id + '", "' + _log + '")'
    print '  [insert_err_log] ' + query

    db = sqlite3.connect(db_path)
    db.execute(query)
    db.commit()
    db.close()


def get_user_id(_dirname):
    strlist = _dirname.split('/')
    strlist_len = len(strlist)
    user_id = strlist[strlist_len-1]
    return user_id


def execute(_cmd):
    print '  [execute] ' + _cmd
    fd = subprocess.Popen(_cmd, shell=True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
    stdout, stderr = fd.communicate()
    return stdout, stderr


def delete_dir(_directory):
    cmd = 'rm -rf ' + _directory
    std_out, std_err = execute(cmd)


def first_offset(test_file):
    while True:
        line = test_file.readline()
        if not line:
            break
        if bool(re.search(r'^\s*\#\s*\d+', line)):
            break

def next_list(_testfile, _n):
    list = []

    first_offset(_testfile)
    for i in range(1, _n+1):
        line = _testfile.readline()
        if not line:
            list.append('EOF')
            break
        line = line.replace(',', '')
        line = line.replace(' ', '')
        line = line.strip()
        line = str(i) + line
        list.append(line)

    return list


def get_nr_solutions(_testfile):
    nr_solutions = 0
    lines = _testfile.readlines()
    expression = '^\s*\#\s*(?P<number>\d+)'
    re_compile = re.compile(expression)

    for line in lines:
        re_match = re_compile.match(line)
        if re_match:
            nr_solutions = int(re_match.group('number'))
    _testfile.seek(0, os.SEEK_SET)
    return nr_solutions
            

def accuracy_test(_directory, _n):
    total_count = 0

    if _n == 8:
        answer_file = open('solutions/solution-8', 'r')
        candidate_file = open(_directory + '/result-8.out', 'r')
    elif _n == 11:
        answer_file = open('solutions/solution-11', 'r')
        candidate_file = open(_directory + '/result-11.out', 'r')
    elif _n == 13:
        answer_file = open('solutions/solution-13', 'r')
        candidate_file = open(_directory + '/result-13.out', 'r')
    else:
        print '  [accuracy_test] unexpected N'
        return False

    nr_solutions = get_nr_solutions(answer_file)

    msg = '  [accuracy_test] N=' + str(_n) 
    msg += ', nr_solutions=' + str(nr_solutions)
    print msg

    while True:
        answer_list = next_list(answer_file, _n)

        if answer_list[0] == 'EOF':
            break

        candidate_file.seek(0, os.SEEK_SET)

        while True:
            candidate_list = next_list(candidate_file, _n)

            if candidate_list[0] == 'EOF':
                break

            cnt = 0
            for j in range(0, _n):
                if answer_list[j] == candidate_list[j]:
                    cnt = cnt + 1
            if cnt == _n:
                total_count = total_count + 1

    answer_file.close()
    candidate_file.close()

    if total_count == nr_solutions:
        print '  [accuracy_test] Accuracy Test Success'
        return True
    else:
        print '  [accuracy_test] Accuracy Test Fail'
        return False


def main():
    while True:
        dirs_list = []
        
        print '\n[main] It is waiting for a job...'

        for dirname, dirnames, filenames in os.walk('source_code'):
            # print path to all subdirectories first.
            for subdirname in dirnames:
                dirs_list.append(os.path.join(dirname, subdirname))

        dirs_count =  len(dirs_list)
        
        remain_count = 0
        remain_jobs = []
        for directory in dirs_list:
            if os.path.exists(directory + '/nqueens'):
                remain_count = remain_count + 1
                remain_jobs.append(directory)

        print '[main] remaining jobs : ' + str(remain_count)
        print '\t',
        print remain_jobs

        for i in range(1, dirs_count):
            dirname = dirs_list.pop()

            for _dirname, _dirnames, filenames in os.walk(dirname):
                for filename in filenames:
                    if filename == 'nqueens':
                        print '[main] Testing is started : ' + dirname
                        user_id = get_user_id(dirname)

                        # N=8
                        cmd = 'time ' + dirname + '/nqueens 8 > '
                        cmd += dirname + '/result-8.out'
                        std_out, std_err = execute(cmd)

                        # N=11
                        cmd = 'time ' + dirname + '/nqueens 11 > '
                        cmd += dirname + '/result-11.out'
                        std_out, std_err = execute(cmd)

                        # N=13
                        cmd = 'time ' + dirname + '/nqueens 13 > '
                        cmd += dirname + '/result-13.out'
                        std_out, std_err = execute(cmd)
                        std_err = std_err.strip()

                        print '[main] time : ' + std_err

                        expression = '\d+\.\d+user\s+\d+\.\d+system'
                        expression += '\s+(?P<minute>\d+):'
                        expression += '(?P<second>\d+\.\d+)elapsed\s'
                        re_compile = re.compile(expression)
                        re_search = re_compile.search(std_err)
                        minute = float(re_search.group('minute'))
                        second = float(re_search.group('second'))
                        elapsed_time = minute * 60 + second

                        accuracy1 = accuracy_test(dirname, 8)
                        accuracy2 = accuracy_test(dirname, 11)
                        accuracy3 = accuracy_test(dirname, 13)

                        if accuracy1 & accuracy2 & accuracy3:
                            # Record the result
                            insert_entry(user_id, elapsed_time)
                            rename_src = dirname + '/nqueens'
                            rename_dst = dirname + '/nqueens-finish'
                            print '[main] ' + rename_src + ' -> ' + rename_dst
                            os.rename(rename_src, rename_dst)
                            print '[main] ' + user_id + ', ' + str(elapsed_time)
                        else:
                            # Record the error log
                            log = 'Accuracy test failed'
                            insert_error_log(user_id, log)
                            # Delete files the test has been completed 
                            delete_dir(dirname)
                            print '[main] The result is wrong.'

        time.sleep(10)
           
if __name__ == '__main__':
    main()
    
