import numpy

from OMEXMLreader import OMEXMLReader
from customreader import CustomReader

class VTITIFReader(OMEXMLReader, CustomReader):
    ftype = "tif"

    @property
    def fps(self):
        if self.interval:
            return 1.0/self.interval

    def _get_typespecific_extra_info(self):
        #reset description because it contains all frame timings
        self.description = ""
        timing_text = self.et.find(self.fulltags["Image/Description"]).text.split('\n')
        self.frame_times = {}
        begin = False
        for line in timing_text:
            if not line:
                continue
            if not begin:
                if "Frame Time" in line:
                    #header for timings found. Start reading frame times
                    begin = True
                else:
                    continue
            else:
                frame_info = line.split(" ")
                frame_no = int(frame_info[0])
                frame_time = float(frame_info[1])
                self.frame_times[frame_no] = frame_time
        times_sorted = []
        frames = self.frame_times.keys()
        frames.sort()
        for frame_no in frames:
            times_sorted.append(self.frame_times[frame_no])
        deltas = numpy.diff(times_sorted)
        #print "\n\nAverage frame time: %f"%deltas.mean()
        #print "FPS: %f"%(1.0/deltas.mean())
        self.description = "FPS: %i Frames: %i"%(1.0/deltas.mean(),len(frames))
        self.interval = deltas.mean()*1000#convert to ms





