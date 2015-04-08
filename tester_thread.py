__author__ = 'Jungsik Choi'

import threading
import time
import subprocess
import re

class ProgramTester(threading.Thread):
    def __init__(self, _db, _dir):
        threading.Thread.__init__(self)
        self.job_queue = []
        self.db = _db
        self.base_dir = _dir
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


    def accuracy_test(self, _directory):
        nr_solutions = 0
        test_file = open(_directory + '/result.out', 'r')
        lines = test_file.readlines()
        expression = '^\s*\#\s*(?P<number>\d+)'
        re_compile = re.compile(expression)

        for line in lines:
            re_match = re_compile.match(line)
            if re_match:
                nr_solutions = int(re_match.group('number'))

        if nr_solutions == 264:
            return True
        else:
            return False
                
            
    def run(self):
        self.running = True
        print 'tester thread is started!!'
        while True:
            if self.nr_jobs() > 0:
                print 'TEST>> wake up'
                job = self.pop_job()

                # Measure the elapsed time
                directory = self.base_dir + '/' + job
                cmd = 'time ' + directory + '/nqueens 11 > '
                cmd += directory + '/result.out'
                std_out, std_err = self.execute(cmd)
                std_err = std_err.strip()

                expression = '^\d+\.\d+user\s+\d+\.\d+system'
                expression += '\s+(?P<minute>\d+):'
                expression += '(?P<second>\d+\.\d+)elapsed\s'
                try:
                    re_compile = re.compile(expression)
                    re_match = re_compile.match(std_err)
                    minute = float(re_match.group('minute'))
                    second = float(re_match.group('second'))
                    elapsed_time = minute * 60 + second
                except Exception as inst:
                    print type(inst)
                    print 'TEST>> Error'

                else:
                    accuracy = self.accuracy_test(directory)
                    # Delete files the test has been completed 
                    self.delete_dir(directory)

                    if accuracy:
                        # Record the result
                        self.db.insert_entry(job, elapsed_time)
                        print 'TEST>> ' + job + ', ' + str(elapsed_time)
                    else:
                        print 'TEST>> The result is wrong.'

            time.sleep(10)
            
