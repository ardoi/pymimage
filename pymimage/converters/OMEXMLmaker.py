import time
import os
import sys
from subprocess import Popen, PIPE
import logging

from PyQt5 import QtCore as QC



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
        #print "\nSTATUS CHECK"
        #print 'Running', len(self.running_list)
        #print 'Done', len(self.done_list)
        #print 'Torun', len(self.torun_list)
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
        #self.logger.info('%i running, %i done'%(running, len(self.done_list)))

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

class OMEXMLMaker(QC.QObject):
    conversion_finished = QC.pyqtSignal()
    conversion_update = QC.pyqtSignal()
    set_file_being_inspected_label = QC.pyqtSignal(str)
    filesConverted = QC.pyqtSignal(int)

    def __init__(self, parent = None, signals = True):
        super(OMEXMLMaker, self).__init__(parent)
        if hasattr(sys, 'frozen'):
            #windows package created with pyinstaller. In order to access bftools a different approach is needed
            tool_dir = os.path.normpath(os.path.join(os.path.dirname(sys.executable),'bftools'))
        else:
            tool_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)),'..','..','..','lib','bftools'))
        self.convert_cmd = os.path.join(tool_dir,'bfconvert')+' -no-upgrade -compression zlib  "{0}" "{1}"'
        self.toconvert = {}
        self.logger = logging.getLogger(__name__)
        if not self.logger.root.handlers and not self.logger.handlers:
            hh = logging.StreamHandler(sys.stdout)
            log_format = "%(levelname)s:%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(message)s"
            hh.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(hh)
            self.logger.setLevel(logging.DEBUG)
        self.logger.info("OMXMLMaker created")
        self.logger.info('Bioformats directory is: {}'.format(tool_dir))
        self.done = 0
        self.signals = signals

    def reset_convert_list(self):
        self.toconvert = {}

    def add_file_to_convert(self, caller):
        #caller is dummyreader instance who added file to be converted. it needs to be notified when file is done
        self.toconvert[caller.file_name] = caller

    def check_progress(self):
        for f in self.shellrunners.keys():
            if self.shellrunners[f].done == True:
                continue
            if self.shellrunners[f].is_done():
                self.files_to_convert.remove(f)
                self.logger.debug('%i files left to convert'%len(self.files_to_convert))
                self.logger.debug("\n".join(self.files_to_convert))
                if self.files_to_convert:
                    print 'running ', self.herder.running_list
                    running_names = []
                    for runner in self.herder.running_list:
                        running_names.append(bfconvert_filename_from_runner(runner))
                    running_string = ", ".join(running_names)
                    self.set_file_being_inspected_label.emit(running_string)
                else:
                    self.set_file_being_inspected_label.emit("Done")

                res = self.shellrunners[f].result()
                if res[0] == 1:
                    self.logger.error('File %s failed to convert'%f)
                    self.logger.error('Command: '+self.shellrunners[f].command)
                    self.logger.error(res[1])
                    omename = [el for el in self.shellrunners[f].command.split('"') if el.strip()][-1]
                    if os.path.isfile(omename):
                        os.remove(omename)
                        self.logger.error('Removing failed conversion result: %s'%omename)
                    self.toconvert[f].set_conversion_failed()
                else:
                    self.logger.info(res[2])
                    self.toconvert[f].check_for_ome()
                self.done += 1
                self.filesConverted.emit(self.done)
        if not self.herder.check_status():
            if self.signals:
                self.timer.stop()
            self.wrap_up_conversion()
        self.conversion_update.emit()

    def convert_all(self):
        self.time0 = time.time()
        self.done = 0
        self.shellrunners = {}
        self.herder = RunnerHerder(3)
        self.files_to_convert = self.toconvert.keys()
        self.files_to_convert.sort()
        for f in self.files_to_convert:
            #ome_dir = self.ome_dir_name(f)
            microscope_image = self.toconvert[f]
            ome_name = microscope_image.ome_full_name
            f_out = ome_name
            #check if file really needs converting
            if os.path.isfile(f_out):
                print "%s already converted to %s"%(f,f_out)
            else:
                print "Converting %s to %s"%(f,f_out)
                run_cmd = self.convert_cmd.format(f,f_out)
                print run_cmd
                #QC.QTimer.singleShot(500,lambda :convert(run_cmd))
 #               convert(run_cmd)
                #if len(self.shellrunners) == 0:
                #    self.emit(QC.SIGNAL('set_file_being_inspected_label(QString)'),\
                #            str(os.path.basename(f)))
                runner = ShellRunner(run_cmd)
                self.shellrunners[f] = runner
                self.herder.add_runner(runner)
        self.herder.check_status()
        self.logger.info('%i files need conversion'%len(self.shellrunners))
        if self.herder.torun_list:
            lll = [el for el in self.herder.torun_list[-1].command.split('"') if el.strip()]
            filename = lll[-2]
        else:
            filename = ""
        if self.signals:
            self.set_file_being_inspected_label.emit(str(os.path.basename(filename)))
            self.timer = QC.QTimer()
            self.timer.timeout.connect(self.check_progress)
            self.timer.start(1000)
            self.filesConverted.emit(self.done)
        else:
            while self.toconvert:
                time.sleep(5)
                self.check_progress()

    def wrap_up_conversion(self):
        self.logger.info('Total time taken by conversion %.1f seconds'%(time.time()-self.time0))
        self.conversion_finished.emit()
        self.toconvert = {}


