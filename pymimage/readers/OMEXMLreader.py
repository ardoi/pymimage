#from xml.etree.ElementTree import ElementTree, ParseError
import xml.etree.ElementTree as ElementTree
import base64
import StringIO
import zlib
import datetime
import os
import logging

import numpy


class OMEXMLReader(object):
    #OME-XML namespace stuff
    ns = "{http://www.openmicroscopy.org/Schemas/OME/2012-06}"
    nsa = "{http://www.openmicroscopy.org/Schemas/SA/2012-06}"
    nsb = "{http://www.openmicroscopy.org/Schemas/BinaryFile/2012-06}"
    nsr = "{http://www.openmicroscopy.org/Schemas/ROI/2012-06}"
    nso = "{openmicroscopy.org/OriginalMetadata}"
    tags = {'Image': ns + "Image", 'Pixels': ns + "Pixels", 'BinData': nsb + "BinData", 'Channel': ns + "Channel",
            "TiffData":ns+"TiffData",
            'StructuredAnnotations': nsa + "StructuredAnnotations",
            'XMLAnnotation': nsa + "XMLAnnotation",
            "MDKey": nso + "Key", "MDValue": nso + "Value", "AcquisitionDate": ns + "AcquisitionDate",
            "Value": nsa + "Value", "OriginalMetadata": nso + "OriginalMetadata",
            "Description": ns + "Description", "ROI":nsr+"ROI", "Union":nsr+"Union", "Shape":nsr+"Shape", "Line":nsr+"Line"}

    def __init__(self, filename):
        self.filename = filename
        self.image_attrs = {}
        self.images = {}
        self.active_image_number = None
        self.logger = logging.getLogger(__name__)
    @property
    def pixels(self):
        return self.image_width*self.image_height
    @property
    def image_width(self):
        return self.image_attrs[self.active_image_number]["image_width"]

    @image_width.setter
    def image_width(self, val ):
        self.image_attrs[self.active_image_number]["image_width"] = val

    @property
    def image_height(self):
        return self.image_attrs[self.active_image_number]["image_height"]

    @image_height.setter
    def image_height(self, val ):
        self.image_attrs[self.active_image_number]["image_height"] = val

    @property
    def channels(self):
        return self.image_attrs[self.active_image_number]["channels"]

    @channels.setter
    def channels(self, val ):
        self.image_attrs[self.active_image_number]["channels"] = val

    @property
    def frames(self):
        return self.image_attrs[self.active_image_number]["frames"]

    @frames.setter
    def frames(self, val ):
        self.image_attrs[self.active_image_number]["frames"] = val

    @property
    def data_type(self):
        return self.image_attrs[self.active_image_number]["data_type"]

    @data_type.setter
    def data_type(self, val ):
        self.image_attrs[self.active_image_number]["data_type"] = val

    @property
    def image_step_y(self):
        return self.image_attrs[self.active_image_number]["image_step_y"]

    @image_step_y.setter
    def image_step_y(self, val ):
        self.image_attrs[self.active_image_number]["image_step_y"] = val

    def read_meta(self):
        self.ome_type = os.path.splitext(self.filename)[-1]
        #based on whether we are opeing a OME-XML or OME-TIFF file the tags contained in the XML are different
        #if self.ome_type == ".tiff":
        #    self.bintagname = "TiffData"
        #elif self.ome_type == ".ome":
        if self.ome_type == ".ome":
            self.bintagname = "BinData"
        else:
            raise ValueError("unknown extension %s"%self.ome_type)
        if self.bintagname == "TiffData":
            pass
            #self.pil_image = Image.open(self.filename)
            #image_description_tag = 270
            #self.et = xmle.fromstring(self.pil_image.tag[image_description_tag])
        else:
            try:
                self.et = ElementTree.ElementTree()
                self.et.parse(self.filename)
            except ElementTree.ParseError:
                with open(self.filename,'r') as f:
                    lines = f.readlines()
                    bad = {'&':"_and_"}
                    for i,line in enumerate(lines):
                        change = True in [bad_char in line for bad_char in bad.keys()]
                        if change:
                            data = line.replace("&","_and_")
                            lines[i] = data
                    self.et=ElementTree.fromstringlist(lines)
        self.fulltags = {}
        self._make_tags()
        self._get_image_attributes()
        self.metadata_loaded = True

    def _make_tag(self, name):
        names = name.split("/")
        if len(names) > 1:
            taglist = [OMEXMLReader.tags[el] for el in names]
            tag = "/".join(taglist)
            return tag
        else:
            return OMEXMLReader.tags[names[0]]

    def _make_tags(self):
        names = ["Image", "Image/Pixels", "BinData", "Image/AcquisitionDate", "Image/Description",
                 "StructuredAnnotations/XMLAnnotation/Value/OriginalMetadata", "MDKey", 'MDValue', "Pixels", "Channel",
                 "AcquisitionDate",'TiffData', "ROI/Union/Shape/Line"]
        for name in names:
            self.fulltags[name] = self._make_tag(name)

    def _get_image_attributes(self):
        """
        Reads image information from the ome file. Square images are assumed to be the reference image (recorded by the
        microscope before a linescan). Linescan image is used for the general image attributes as those are the ones
        relevant to analysis.
        """
        self.logger.info("Reading image attributes for image {}".format(self.filename))
        image_elements = self.et.findall(self.fulltags["Image"])
        for im_n, image_element in enumerate(image_elements):
            pixels = image_element.findall(self.fulltags["Pixels"])
            bindata_dict = {}
            image_stuff = {"Attributes": image_element.attrib,# "Channels": channel_dict,
                    "BinDatas": bindata_dict, "ImageData": None}
            for pi_n, pixel in enumerate(pixels):
                #There is only one pixel element per Image (although the schema allows more)
                #TODO In the next OME release Pixel data will be moved up to Image

                #channels = pixel.findall(self.fulltags["Channel"])
                #for ch_n, channel in enumerate(channels):
                #    channel_dict[ch_n] = channel
                bindatas = pixel.findall(self.fulltags[self.bintagname])
                for bin_n, bindata in enumerate(bindatas):
                    if self.bintagname == "BinData":
                        if int(bindata.attrib["Length"]) > 0:
                            bindata_dict[bin_n] = bindata
                    #else:
                    #    tiffdata_dict[bin_n] = tiffdata
                image_stuff["PixelAttributes"] = pixel.attrib
                self.image_attrs[im_n]={}
            self.images[im_n] = image_stuff
            self.active_image_number = im_n
            #we can do this because we know only one Pixel element exists per Image
            pix_attr = self.images[self.active_image_number]["PixelAttributes"]
            self.image_width = int(pix_attr['SizeX'])
            self.image_height = int(pix_attr['SizeY'])
            self.channels = int(pix_attr['SizeC'])
            self.frames = int(pix_attr['SizeT'])
            self.data_type = pix_attr["Type"]
            try:
                self.image_step_x = float(pix_attr['PhysicalSizeX'])
            except KeyError:
                self.image_step_x = None
            try:
                self.image_step_y = float(pix_attr['PhysicalSizeY'])
            except KeyError:
                self.image_step_y = None
            message = "Image {}: {} x {} pixels ({} total), {} channels, {} frames".\
                    format(self.active_image_number, self.image_width, self.image_height,
                           self.pixels, self.channels, self.frames)
            if self.image_step_x and self.image_step_y:
                message+=", dx:dy = {} : {}".format(self.image_step_x, self.image_step_y)
            self.logger.info(message)
        self.image_name = self.images[0]["Attributes"]["Name"]
        date = image_elements[0].find(self.fulltags["AcquisitionDate"]).text
        self.datetime = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        #print "attributes=",self.image_attrs

        try:
            self.description = self.et.find(self.fulltags["Image/Description"]).text
        except AttributeError:
            self.description = ""
            pass
        self.active_image_number = 0
        self._get_extra_info()
        #if images["Reference"]:
        #    #try to get ROI
        #    roi_element = self.et.find(self.fulltags["ROI/Union/Shape/Line"])
        #    #print "ROI element", roi_element is None
        #    if roi_element is not None:
        #        roi_attrib = roi_element.attrib
        #        #print roi_attrib
        #        roi = {"x2":float(roi_attrib["X2"]),"x1":float(roi_attrib["X1"]),
        #                "y2":float(roi_attrib["Y2"]), "y1":float(roi_attrib["Y1"])}
        #        images["Reference"]["ROI"] = roi
        #    else:
        #        images["Reference"]["ROI"] = None


    def read_image(self, image_type):
        self.active_image_number = image_type
        if not self.metadata_loaded:
            self.read_meta()
        if self.images[image_type]:
            #print self.images[image_type]["ImageData"]
            if self.images[image_type]["ImageData"]  is None:
                self._get_image_data(image_type)


    def _get_image_data(self, image_type):
        self.logger.info("Reading data for image {}".format(self.active_image_number))
        tiffdata_elements = self.images[image_type]["BinDatas"]
        data_array = numpy.zeros(shape=(self.channels, self.frames, self.image_height, self.image_width),
                dtype=self.data_type)
        print 'zero data', data_array.shape
        #print data_array.shape
        self.images[image_type]["ImageData"] = data_array
        for tiffdata_element_key in tiffdata_elements:
            #since ome does not group bindatas in channels we have to guess which bindata elements are in which channel.
            #assuming that all frames from one channel are grouped together so we have self.frames frames in each channel.
            #Once self.frames number of frames have been read then switch to the next channel
            frame = tiffdata_element_key % self.frames
            channel = tiffdata_element_key / self.frames
            tiffdata_element = tiffdata_elements[tiffdata_element_key]
            bin_attrib = tiffdata_element.attrib
            #print 'bin attrib',bin_attrib
            if self.bintagname == "BinData":
                compression = None
                if 'Compression' in bin_attrib:
                    compression = bin_attrib['Compression']
                    #print 'Compressed with %s' % compression
                else:
                    pass
                    #print 'Not compressed'
                #data_length = int(bin_attrib['Length'])
                dtype = self.data_type
                #dtype_size = numpy.dtype(dtype).itemsize
                #print 'Total data %s' % data_length
                #decode base64 data
                stringio_in = StringIO.StringIO(tiffdata_element.text)
                stringio_out = StringIO.StringIO()
                base64.decode(stringio_in, stringio_out)
                if compression:
                    image_data = numpy.fromstring(zlib.decompress(stringio_out.getvalue()),
                            dtype).astype('float32')
                else:
                    image_data = numpy.fromstring(stringio_out.getvalue(), dtype).astype('float32')
            #elif self.bintagname == "TiffData":
            #    ifd = int(bin_attrib["IFD"])
            #    self.pil_image.seek(ifd)
            #    image_data = numpy.array(self.pil_image.getdata(),'float')
            #Need to read image dimension from PixelAttribute as they are different for different image types
            image_width = int(self.images[image_type]["PixelAttributes"]["SizeX"])
            image_height = int(self.images[image_type]["PixelAttributes"]["SizeY"])
            print "original_shape", image_data.shape
            image_data.shape = (image_height, image_width)
            print "Image dimensions", image_data.shape
            #print "channel: %i of %i , frame: %i of %i"%(channel+1, self.channels,frame+1, self.frames)
            #self.images[image_type]["ImageData"][channel][frame] = image_data.transpose()
            #data_array[channel][frame] = image_data.transpose()
            data_array[channel][frame] = image_data

        print "\n\n%s\nRead %i channels\n%i frames in each channel\n%ix%i pixels in each frame\n%i MB for entire array\n" % \
                ("="*10,self.channels, self.frames, self.image_width, self.image_height, data_array.nbytes/1024**2)

    def _get_extra_info(self):
        self.annotation_elements = self.et.findall(
            self.fulltags["StructuredAnnotations/XMLAnnotation/Value/OriginalMetadata"])
        self.raw_annotation = {}
        for element in self.annotation_elements:
            keyin = element.find(self.fulltags["MDKey"]).text
            if self.image_name in keyin:
                key = keyin.split(self.image_name)[-1].strip()
            else:
                key = keyin
            self.raw_annotation[key] = element.find(self.fulltags["MDValue"]).text
            #raw_keys = self.raw_annotation.keys()
        #raw_keys.sort()
        self._get_typespecific_extra_info()



