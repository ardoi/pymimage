import numpy

from OMEXMLreader import OMEXMLReader
from customreader import CustomReader


class OIBReader(OMEXMLReader, CustomReader):
    ftype = ["oib", "oif"]
    def _get_typespecific_extra_info(self):
        raw_keys = self.raw_annotation.keys()
        raw_keys.sort()
        frame_time = None
        for key in raw_keys:
            if 'Time Per Frame' in key:
                frame_time = float(self.raw_annotation[key]) * 1e-3 #OIB saves time in microseconds, but we want milliseconds
                break
            else:
                pass
        if frame_time:
            #FIXME Temporary fix to get right line time
            self.timestamps = frame_time / float(self.image_height) * numpy.arange(self.image_height)
            self.interval = numpy.diff(self.timestamps)[1]
        else:
            self.timestamps = None
            self.interval = None


