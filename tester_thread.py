__author__ = 'Jungsik Choi'

import threading
import time
import subprocess
import re
import os

class ProgramTester(threading.Thread):
    def __init__(self, _db, _dir, _n, _example_path):
        threading.Thread.__init__(self)
        self.job_queue = []
        self.db = _db
        self.base_dir = _dir
        self.n = _n
        self.example_path = _example_path
        self.running = False

    def nr_jobs(self):
        return len(self.job_queue)

    def push_job(self, _job):
        try:
            self.job_queue.append(_job)
        except Exception as inst:
            print type(inst)
            msg = 'TEST>> push queue error'
            msg += _job
            print msg
            return False
        else:
            return True


    def pop_job(self):
        try:
            job = self.job_queue.pop(0)
        except Exception as inst:
            print type(inst)
            msg = 'TEST>> pop queue error'
            print msg
            return False
        else:
            return job
            

    def execute(self, _cmd):
        print ' EXE>> ' + _cmd
        fd = subprocess.Popen(_cmd, shell=True,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE)
        self.stdout, self.stderr = fd.communicate()
        return self.stdout, self.stderr


    def delete_dir(self, _directory):
        cmd = 'rm -rf ' + _directory
        std_out, std_err = self.execute(cmd)


    def first_offset(self, test_file):
        while True:
            line = test_file.readline()
            if not line:
                break
            if bool(re.search(r'^\s*\#\s*\d+', line)):
                break

    def next_list(self, _testfile, _n):
        list = []

        self.first_offset(_testfile)
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


    def get_nr_solutions(self, _testfile):
        print '[get_nr_solutions] ',
        print _testfile
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
                

    def accuracy_test(self, _directory, _n):
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
            print 'TEST>> unexpected N'
            return False

        nr_solutions = self.get_nr_solutions(answer_file)

        msg = '[accuracy_test] N=' + str(_n) 
        msg += ', nr_solutions=' + str(nr_solutions)
        print msg

        while True:
            answer_list = self.next_list(answer_file, _n)

            if answer_list[0] == 'EOF':
                break

            candidate_file.seek(0, os.SEEK_SET)

            while True:
                candidate_list = self.next_list(candidate_file, _n)

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
            print '[accuracy_test] Accuracy Test Success'
            return True
        else:
            print '[accuracy_test] Accuracy Test Fail'
            return False

            
    def run(self):
        self.running = True
        accuracy1 = False
        accuracy2 = False
        accuracy3 = False

        print 'tester thread is started!!'
        time.sleep(1)
        while True:
            print "TEST>> It's waiting for jobs"
            if self.nr_jobs() > 0:
                print 'TEST>> wake up'
                job = self.pop_job()

                # Measure the elapsed time
                directory = self.base_dir + '/' + job

                # N=8
                cmd = 'time ' + directory + '/nqueens 8 > '
                cmd += directory + '/result-8.out'
                std_out, std_err = self.execute(cmd)

                # N=11
                cmd = 'time ' + directory + '/nqueens 11 > '
                cmd += directory + '/result-11.out'
                std_out, std_err = self.execute(cmd)

                # N=13
                cmd = 'time ' + directory + '/nqueens 13 > '
                cmd += directory + '/result-13.out'
                std_out, std_err = self.execute(cmd)
                std_err = std_err.strip()

                print 'TEST>> ' + std_err

                expression = '\d+\.\d+user\s+\d+\.\d+system'
                expression += '\s+(?P<minute>\d+):'
                expression += '(?P<second>\d+\.\d+)elapsed\s'
                re_compile = re.compile(expression)
                re_search = re_compile.search(std_err)
                minute = float(re_search.group('minute'))
                second = float(re_search.group('second'))
                elapsed_time = minute * 60 + second

                accuracy1 = self.accuracy_test(directory, 8)
                accuracy2 = self.accuracy_test(directory, 11)
                accuracy3 = self.accuracy_test(directory, 13)

                if accuracy1 & accuracy2 & accuracy3:
                    # Record the result
                    self.db.insert_entry(job, elapsed_time)
                    print 'TEST>> ' + job + ', ' + str(elapsed_time)
                else:
                    # Delete files the test has been completed 
                    self.delete_dir(directory)
                    print 'TEST>> The result is wrong.'

            time.sleep(10)
            
