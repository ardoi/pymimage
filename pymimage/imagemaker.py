import os
import hashlib
import logging

from readers.customreader import CustomReader

class ImageMaker(object):
    bytes_to_read = 1024**2
    hash_digits = 10
    plugin_folder = os.path.join("readers","custom")
    plugin_folder = "pymimage/readers"

    def __init__(self, ome_dir):
        self.ome_dir = ome_dir
        #CustomReader.load(ImageMaker.plugin_folder)
        import readers.LSMreader
        import readers.OIBreader
        import readers.VTITIFreader
        print 'im',CustomReader.registered


    @staticmethod
    def get_hash(filename):
        if os.path.isfile(filename):
            with open(filename,'rb') as f:
                data = f.read(ImageMaker.bytes_to_read)
                fhash = hashlib.sha1(data).hexdigest()[:ImageMaker.hash_digits]
                return fhash
        else:
            raise IOError("No such file: %s"%filename)


    def check_for_ome(self, file_name, force_reader = None):
        file_hash = ImageMaker.get_hash(file_name)
        ome_name = "{}.ome".format(file_hash)
        ome_full_name = os.path.join(self.ome_dir,ome_name )
        if os.path.isfile(ome_full_name):
            logging.info('Ome file %s found for image %s'%(ome_name, file_name))
            if force_reader:
                reader = force_reader
            else:
                reader = CustomReader.get_reader(file_name)
            ome_file = reader(ome_full_name)
            return ome_file
        else:
            logging.info('No OME file %s found for image %s'%(ome_name, file_name))
            return None

    @staticmethod
    def load_dir(dir_name):
        pass

    @staticmethod
    def load_files(filenames):
        pass

    @staticmethod
    def load_file(filename):
        pass


