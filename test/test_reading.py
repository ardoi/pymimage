import os
from pymimage.imagemaker import ImageMaker
from nose.tools import raises


def test_hash():
    filename = os.path.join("test", "data", "Image0035.oib")
    assert ImageMaker.get_hash(filename) == "e06250156e"


class TestOIBConversion():

    @classmethod
    def setup_class(cls):
        "Remove existing file"
        ome_name = os.path.join("tmp", "e06250156e.ome")
        try:
            pass
            os.remove(ome_name)
        except OSError:
            pass

    def setup(self):
        self.filename = os.path.join("test", "data", "Image0035.oib")
        self.imaker = ImageMaker("tmp")
        self.ome_name = os.path.join("tmp", "e06250156e.ome")
        self.ome_file = self.imaker.load_file(self.filename)

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


class TestMissingFileConversion():

    def setup(self):
        self.filename = os.path.join("test", "data", "nosuchfile.oib")
        self.imaker = ImageMaker("tmp")

    @raises(IOError)
    def test_load(self):
        self.ome_file = self.imaker.load_file(self.filename)


class TestInvalidFileConversion():

    def setup(self):
        self.filename = os.path.join("test", "data", "invalid.oib")
        self.imaker = ImageMaker("tmp")

    def test_load(self):
        self.ome_file = self.imaker.load_file(self.filename)
        assert self.ome_file is None
