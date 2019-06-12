import logging
import os

from pymimage.readers.OMEXMLreader import OMEXMLReader

class CustomReader(object):
    """Base class for readers that need to do some custom processing of the image data."""

    registered = []

    def __init__(self, name, base, attrs):
        self.registered.append(self)

    @classmethod
    def get_reader(cls, file_name):
        extension = os.path.splitext(file_name)[-1].split('.')[-1].lower()
        suitable = []
        logger = logging.getLogger(__name__)
        for reader in cls.registered:
            if isinstance(reader.ftype, str):
                reader_types = [reader.ftype]
            else:
                reader_types = reader.ftype
            for ftype in reader_types:
                if ftype == extension:
                    suitable.append(reader)
        if len(suitable) > 1:
            message = "More than one reader found for file type {}: {}".\
                    format(extension, ", ".join([cl.__name__ for cl in suitable]))
            logger.warning(message)
        if suitable:
            reader = suitable[0]
        else:
            reader = OMEXMLReader
        logger.info("Using reader: {}".format(reader.__name__))
        return reader

