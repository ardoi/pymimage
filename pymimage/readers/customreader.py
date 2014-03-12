import logging
import os

from OMEXMLreader import OMEXMLReader

class CustomReader(object):
    """Base class for readers that need to do some custom processing of the image data."""

    class __metaclass__(type):
        def __init__(cls, name, base, attrs):
            print base
            if not hasattr(cls, 'registered'):
                cls.registered = []
            else:
                cls.registered.append(cls)

    @classmethod
    def get_reader(cls, file_name):
        extension = os.path.splitext(file_name)[-1].split('.')[-1].lower()
        suitable = []
        for reader in cls.registered:
            if isinstance(reader.ftype, str):
                reader_types = [reader.ftype]
            else:
                reader_types = reader.ftype
            for ftype in reader_types:
                if ftype == extension:
                    suitable.append(reader)
        if len(suitable)>1:
            message = "More than one reader found for file type {}: {}".\
                    format(extension, ", ".join([cl.__name__ for cl in suitable]))
            logging.warning(message)
        if suitable:
            reader = suitable[0]
        else:
            reader = OMEXMLReader
        logging.info("Using reader: {}".format(reader.__name__))
        return reader

