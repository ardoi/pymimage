from subprocess import Popen, PIPE
import logging
import os
import sys
import time



class RunnerHerder:
    def __init__(self, run_at_once=1):
        self.run_at_once = run_at_once
        self.done_list = []
        self.torun_list = []
        self.running_list = []
        self.all_done = False
        self.runners = 0
        self.logger = logging.getLogger(__name__)

    def add_runner(self, runner):
        self.torun_list.append(runner)
        self.runners += 1

    def check_status(self):
        running = 0
        remove_from_running=[]
        for runner in self.running_list:
            if runner.running:
                running += 1
            if runner.done:
                self.done_list.append(runner)
                remove_from_running.append(runner)
        for r in remove_from_running:
            self.running_list.remove(r)
        self.logger.info('%i running, %i done'%(running, len(self.done_list)))

        if len(self.done_list) == self.runners:
            self.logger.debug('Conversion process for %i files finished'%self.runners)
            return 0
        elif not self.torun_list and self.running_list:
            self.logger.debug('All %i conversion processes started'%self.runners)
            self.all_started = True
            return len(self.running_list)
        else:
            while running < self.run_at_once and self.torun_list:
                self.running_list.append(self.torun_list[-1])
                r=self.torun_list.pop()
                r.start()
                running += 1
            if running > self.run_at_once:
                self.logger.error('This many jobs should not be running (%i)'%running)
            return running + len(self.torun_list)


class ShellRunner:
    def __init__(self, command):
        self.done = False
        self.command = command
        self.running = False
        self.p = None
    def start(self):
        self.p = Popen(self.command, shell=True, stdout=PIPE, stderr=PIPE)
        self.running = True
    def is_done(self):
        if not self.p or self.p.poll() is None:
            return False
        else:
            self.done = True
            self.running = False
            return True
    def result(self):
        err = self.p.stderr.read()
        out = self.p.stdout.read()
        return [self.p.returncode,err,out]

def bfconvert_filename_from_runner(runner):
    command = runner.command
    name = os.path.basename(command.split('"')[1])
    return name




class OMEXMLMaker(object):

    def __init__(self):
        if hasattr(sys, 'frozen'):
            #windows package created with pyinstaller. In order to access bftools a different approach is needed
            self.tool_dir = os.path.normpath(os.path.join(os.path.dirname(sys.executable),'bftools'))
        else:
            self.tool_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)),'..','..','bftools'))
        self.convert_cmd = os.path.join(self.tool_dir,'bfconvert')+' -no-upgrade -compression zlib  "{0}" "{1}"'
        self.toconvert = {}
        self.converted = []
        self.failed = []
        self.logger = logging.getLogger(__name__)
        #if not self.logger.root.handlers and not self.logger.handlers:
        #    hh = logging.StreamHandler(sys.stdout)
        #    log_format = "%(levelname)s:%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(message)s"
        #    hh.setFormatter(logging.Formatter(log_format))
        #    self.logger.addHandler(hh)
        #    self.logger.setLevel(logging.DEBUG)
        self.logger.info("OMXMLMaker created")
        self.logger.info( os.path.dirname(__file__))
        self.logger.info('Bioformats directory is: {}'.format(self.tool_dir))
        self.done = 0
        def tools_check(tool_dir):
            cmd = os.path.join(tool_dir, 'bfconvert')
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            retcode = p.wait()
            if retcode==127:
                self.logger.error("Wrong location for bftools: {}".format(tool_dir))
                return False
            return True
        def java_check():
            java_cmd = "java -version"
            p = Popen(java_cmd, shell=True, stdout=PIPE, stderr=PIPE)
            retcode = p.wait()
            if retcode:
                self.logger.error("Java missing. It is needed to convert files into a readable format.")
                return False
            return True
        if not (java_check() and tools_check(self.tool_dir)):
            raise RuntimeError

    def reset_convert_list(self):
        self.toconvert = {}

    def add_file_to_convert(self, file_in, file_out):
        self.toconvert[file_in] = file_out

    def check_progress(self):
        for f in self.shellrunners.keys():
            if self.shellrunners[f].done == True:
                continue
            if self.shellrunners[f].is_done():
                self.files_to_convert.remove(f)
                self.logger.debug('%i files left to convert'%len(self.files_to_convert))
                self.logger.debug("\n".join(self.files_to_convert))

                res = self.shellrunners[f].result()
                if res[0] == 1:
                    self.logger.error('File %s failed to convert'%f)
                    self.logger.error('Command: '+self.shellrunners[f].command)
                    self.logger.error('Error message:{}'.format(res[1]))
                    omename = self.toconvert[f]
                    self.failed.append(f)
                    if os.path.isfile(omename):
                        os.remove(omename)
                        self.logger.warning('Removing failed conversion result: %s'%omename)
                elif res[0] == 127:
                    self.logger.error("bftools not found at {}".format(self.tool_dir))
                    self.failed.append(f)
                else:
                    self.logger.info(res[2])
                    self.converted.append(f)
                self.done += 1
        if not self.herder.check_status():
            self.wrap_up_conversion()


    def convert_all(self):
        self.time0 = time.time()
        self.done = 0
        self.shellrunners = {}
        self.herder = RunnerHerder(3)
        self.files_to_convert = self.toconvert.keys()
        self.files_to_convert.sort()
        for f, f_out in self.toconvert.iteritems():
            if os.path.isfile(f_out):
                self.logger.info("%s already converted to %s"%(f,f_out))
            else:
                self.logger.info("Converting %s to %s"%(f,f_out))
                run_cmd = self.convert_cmd.format(f,f_out)
                self.logger.info("Command: {}".format(run_cmd))
                runner = ShellRunner(run_cmd)
                self.shellrunners[f] = runner
                self.herder.add_runner(runner)
        self.herder.check_status()
        self.logger.info('%i files need conversion'%len(self.shellrunners))
        while self.toconvert:
            time.sleep(2)
            self.check_progress()
        return self.converted,self.failed

    def wrap_up_conversion(self):
        self.logger.info('Total time taken by conversion %.1f seconds'%(time.time()-self.time0))
        self.reset_convert_list()

