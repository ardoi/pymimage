import re

import numpy

from OMEXMLreader import OMEXMLReader
from customreader import CustomReader


class LSMReader(OMEXMLReader, CustomReader):
    ftype = "lsm"

    def _get_typespecific_extra_info(self):
        raw_keys = self.raw_annotation.keys()
        raw_keys.sort()
        raw_timestamps = {}
        raw_events = {}
        for key in raw_keys:
            # collect events
            if 'Event' in key:
                match = re.match("Event(?P<number>\d+)\s(?P<type>\w+)", key)
                if match:
                    event_number = int(match.group('number'))
                    ann_type = match.group('type')
                    if event_number in raw_events:
                        raw_events[event_number].update(
                            {ann_type: self.raw_annotation[key].strip()})
                    else:
                        raw_events.update(
                            {event_number: {ann_type:
                                            self.raw_annotation[key].strip()}})
            # collect timestamps
            elif 'TimeStamp' in key:
                match = re.match("TimeStamp(?P<number>\d+)", key)
                if match:
                    timestamp_group_number = int(match.group('number'))
                    raw_timestamps.update(
                        {int(timestamp_group_number):
                         numpy.fromstring(self.raw_annotation[key], sep=',')})
            elif 'Notes' in key:
                match = re.match("Recording #\d+ Notes", key)
                if match:
                    self.notes = self.raw_annotation[key]
            else:
                pass
                # print key,raw_annotation[key]

        # combine timestamps
        self.event_times = []
        for event_no in raw_events.keys():
            self.event_times.append(float(raw_events[event_no]['Time']))
        print 'events', len(self.event_times)

        timestamp_keys = raw_timestamps.keys()
        timestamp_keys.sort()
        timestamp_list = [raw_timestamps[ts] for ts in timestamp_keys]
        # print raw_timestamps,timestamp_keys
        if timestamp_list:
            # timestamps in seconds, we want ms
            self.timestamps = numpy.hstack(timestamp_list) * 1000
            #v = helpers.find_outliers(s.diff(s.array(self.timestamps)))
            v = numpy.diff(numpy.array(self.timestamps))
            self.interval = v[1]
        else:
            self.timestamps = None
            self.interval = None
