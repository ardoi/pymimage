import os
import sys
from os.path import join, dirname
import pytest
from pymimage.imagemaker import ImageMaker
from nose.tools import raises
import tempfile
import shutil

_filename = __file__


def test_hash():
    filename = join(dirname(_filename), "data", "Image0035.oib")
    assert ImageMaker.get_hash(filename) == "e06250156e"


class TestOIBConversion:

    @classmethod
    def setup_class(cls):
        print(sys.version_info[0])
        print(sys.version_info[0] >= 3)
        cls.filename = join(dirname(_filename), "data", "Image0035.oib")
        cls.temp_dir = tempfile.mkdtemp() if sys.version_info[0] < 3 else tempfile.TemporaryDirectory()
        cls.imaker = ImageMaker(cls.temp_dir if sys.version_info[0] < 3 else cls.temp_dir.name)
        cls.ome_name = join(cls.temp_dir if sys.version_info[0] < 3 else cls.temp_dir.name, "e06250156e.ome")
        cls.ome_file = cls.imaker.load_file(cls.filename)

    @classmethod
    def teardown_class(cls):
        try:
            if sys.version_info[0] >= 3:
                cls.temp_dir.cleanup()
            else:
                shutil.rmtree(cls.temp_dir)
        except OSError as e:
            raise e

    def test_load(self):
        """test"""
        assert self.ome_file is not None
        assert self.ome_file.filename == self.ome_name

    def test_attr(self):
        """The OIB file has two images. Test whether this is true and
        whether their parameters are what they should be. Since image
        has not been read then the ImageData for each image should
        be None"""

        attrib = self.ome_file.image_attrs
        assert 1 in attrib
        assert attrib[0]['frames'] == 1
        assert attrib[0]['channels'] == 1
        assert attrib[0]['image_height'] == 10000
        assert attrib[0]['image_width'] == 344
        assert attrib[0]['image_step_y'] == 0.276
        assert attrib[0]['image_step_x'] == 0.276
        assert self.ome_file.images[0]['ImageData'] is None

        assert 0 in attrib
        assert attrib[1]['frames'] == 1
        assert attrib[1]['channels'] == 1
        assert attrib[1]['image_height'] == 512
        assert attrib[1]['image_width'] == 512
        assert attrib[1]['image_step_y'] == 0.276
        assert attrib[1]['image_step_x'] == 0.276
        assert self.ome_file.images[0]['ImageData'] is None

    def test_data(self):
        """Read image data for both images and check if dimensions
        match what is expected"""
        shapes = ((1, 1, 10000, 344), (1, 1, 512, 512))
        for i in [0, 1]:
            self.ome_file.read_image(i)
            im_data = self.ome_file.images[i]['ImageData']
            im_shape = im_data.shape
            assert im_shape == shapes[i]
            assert im_data.mean() > 0


class TestMissingFileConversion:

    @classmethod
    def setup_class(cls):
        cls.filename = join(dirname(_filename), "data", "nosuchfile.oib")
        cls.temp_dir = tempfile.mkdtemp() if sys.version_info[0] < 3 else tempfile.TemporaryDirectory()
        cls.imaker = ImageMaker(cls.temp_dir if sys.version_info[0] < 3 else cls.temp_dir.name)

    @classmethod
    def teardown_class(cls):
        try:
            if sys.version_info[0] < 3:
                shutil.rmtree(cls.temp_dir)
            else:
                cls.temp_dir.cleanup()
        except OSError as e:
            raise e

    @raises(IOError)
    def test_load(self):
        self.ome_file = self.imaker.load_file(self.filename)


class TestInvalidFileConversion:

    @classmethod
    def setup_class(cls):
        cls.filename = join(dirname(_filename), "data", "invalid.oib")
        cls.temp_dir = tempfile.mkdtemp() if sys.version_info[0] < 3 else tempfile.TemporaryDirectory()
        cls.imaker = ImageMaker(cls.temp_dir if sys.version_info[0] < 3 else cls.temp_dir.name)

    @classmethod
    def teardown_class(cls):
        try:
            if sys.version_info[0] < 3:
                shutil.rmtree(cls.temp_dir)
            else:
                cls.temp_dir.cleanup()
        except OSError as e:
            raise e

    def test_load(self):
        self.ome_file = self.imaker.load_file(self.filename)
        assert self.ome_file is None
