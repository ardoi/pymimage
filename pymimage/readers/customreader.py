import imp
import logging
import pkgutil
import os

from OMEXMLreader import OMEXMLReader

class CustomReader(object):
    """Base class for readers that need to do some custom processing of the image data.
    Plugin framework borrowed from:
    http://rafaelbarreto.wordpress.com/2011/08/25/a-very-lightweight-plug-in-infrastructure-in-python/"""

    class __metaclass__(type):
        def __init__(cls, name, base, attrs):
            print base
            if not hasattr(cls, 'registered'):
                cls.registered = []
            else:
                cls.registered.append(cls)

    @classmethod
    def load(cls, *paths):
        paths = list(paths)
        #cls.registered = []
        #print 'load', paths
        #print 'load', id(cls)
        #print 'load',id(cls.registered)
        #omemod = imp.find_module("OMEXMLreader",paths)
        custommod = imp.find_module("customreader",paths)
        #imp.load_module("OMEXMLreader", omemod[0],omemod[1],omemod[2])
        #imp.load_module("customreader", custommod[0], custommod[1], custommod[2])
        for _, name, _ in pkgutil.iter_modules(paths):
            print '\n',name
            if name in ["customreader", "OMEXMLreader"]:
                continue
            fid, pathname, desc = imp.find_module(name, paths)
            try:
                imp.load_module(name, fid, pathname, desc)
            except Exception as e:
                logging.warning("could not load plugin module '%s': %s",
                                pathname, e.message)
            if fid:
                fid.close()
        #print 'load',cls.registered
        #print 'load',id(cls.registered)

    @classmethod
    def get_reader(cls, file_name):
        extension = os.path.splitext(file_name)[-1].split('.')[-1].lower()
        for reader in cls.registered:
            if isinstance(reader.ftype, str):
                reader_types = [reader.ftype]
            else:
                reader_types = reader.ftype
            for ftype in reader_types:
                if ftype == extension:
                    return reader
        return OMEXMLReader

