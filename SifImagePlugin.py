import numpy as np
from collections import OrderedDict
from PIL import Image, ImageFile

# Read Andor Technology Multi-Channel files with PIL.
# Based on Marcel Leutenegger's MATLAB script.

_MAGIC = 'Andor Technology Multi-Channel File\n'

# --------------------------------------------------------------------
# SIF reader
def _to_string(c):
    ''' convert bytes to string. c: string or bytes'''
    return c if not isinstance(c, bytes) else c.decode('utf-8')

def _read_string(fp, length = None):
    '''Read a string of the given length. If no length is provided, the
    length is read from the file.'''
    if length is None:
        length = int(_to_string(fp.readline()))
    return fp.read(length)

def _read_until_space(fp):
    '''Read a space-delimited word.'''
    word = ''
    while True:
        c = _to_string(fp.read(1))
        if c == ' ' or c == '\n':
            if len(word) > 0:
                break
        word += c
    return word

def _read_int(fp):
    return int(_read_until_space(fp))

def _read_float(fp):
    return float(_read_until_space(fp))


class SifImageFile2(ImageFile.ImageFile):
    format = "SIF"
    format_description = "Andor Technology Multi-Channel File"

    def _open(self):
        if _to_string(self.fp.read(36)) != _MAGIC:
            raise SyntaxError('not a SIF file')

        # 65538 version of andor sif file format
        self.info['SifVersion'] = _read_until_space(self.fp)

        for p in range(5):
            is_present = _read_until_space(self.fp)
            if is_present == '1':
                self.read_instaimage(p)
                self.read_calibimage(p)
                self.read_image_structure(p)

    def read_instaimage(self, p):
        """ read in the instaimage structure data.
        p: index of instaimage.
        """
        info = OrderedDict()
        info['version'] = int(_read_until_space(self.fp))
        info['type'] = int(_read_until_space(self.fp))
        info['active'] = int(_read_until_space(self.fp))
        info['structure_version'] = int(_read_until_space(self.fp))
        info['timedate'] = int(_read_until_space(self.fp))
        info['temperature'] = float(_read_until_space(self.fp))
        info['head'] = self.fp.read(2)
        info['store_type'] = self.fp.read(2)
        info['data_type'] = _read_until_space(self.fp)
        info['mode'] = _read_until_space(self.fp)
        print(info)

class SifImageFile(ImageFile.ImageFile):
    format = "SIF"
    format_description = "Andor Technology Multi-Channel File"

    def _open(self):
        if _to_string(self.fp.read(36)) != _MAGIC:
            raise SyntaxError('not a SIF file')

        # What's this?
        self.fp.readline() # 65538 number_of_images?

        self.info['SifVersion'] = int(_read_until_space(self.fp)) # 65559

        # What's this?
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 1

        self.info['ExperimentTime'] = _read_int(self.fp)
        self.info['DetectorTemperature'] = _read_float(self.fp)

        # What is this?
        _read_string(self.fp, 10) # blank

        # What is this?
        _read_until_space(self.fp) # 0

        self.info['ExposureTime'] = _read_float(self.fp)
        self.info['CycleTime'] = _read_float(self.fp)
        self.info['AccumulatedCycleTime'] = _read_float(self.fp)
        self.info['AccumulatedCycles'] = _read_int(self.fp)

        self.fp.read(1) # NULL
        self.fp.read(1) # space

        self.info['StackCycleTime'] = _read_float(self.fp)
        self.info['PixelReadoutTime'] = _read_float(self.fp)

        # What is this?
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 1
        self.info['GainDAC'] = _read_float(self.fp)

        # What is this?
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 1e-8
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0

        # What is this?
        self.fp.read(1) # 0x04
        self.fp.read(1) # space
        self.fp.read(1) # NULL
        self.fp.read(1) # space

        # What are  these? Related to software/firmware versions?
        _read_until_space(self.fp) # 1 or 512
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 4
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0 or 1
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 500000
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # float
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 1 or 4
        _read_until_space(self.fp) # 0 or 8061
        _read_until_space(self.fp) # 1
        _read_until_space(self.fp) # 1
        _read_until_space(self.fp) # -999
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # -1
        _read_until_space(self.fp) # 4
        _read_until_space(self.fp) # 15
        _read_until_space(self.fp) # 30003
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 1

        try:
            self.info['DetectorType'] = _read_string(self.fp)
            # What is this?
            self.fp.read(3) # space newline space
        except ValueError:
            # support DV420
            self.info['DetectorType'] = _to_string(self.fp.readline())

        self.info['DetectorDimensions'] = (_read_int(self.fp), _read_int(self.fp))

        self.info['OriginalFilename'] = _read_string(self.fp)

        # What is this?
        self.fp.read(2) # space newline
        _read_until_space(self.fp) # 65538

        # What is this?
        _read_string(self.fp) # Is this some type of experiment comment?
        self.fp.read(1) # newline
        _read_int(self.fp) # 65538
        self.fp.read(8) # 0x01 space 0x02 space 0x03 space 0x00 space
        self.info['ShutterTime'] = (_read_float(self.fp), _read_float(self.fp)) # ends in newline

        if (65548 <= self.info['SifVersion'] &
                self.info['SifVersion'] <= 65557):
            for _ in range(2):
                self.fp.readline()
        elif self.info['SifVersion'] == 65558:
            for _ in range(5):
                self.fp.readline()
        elif self.info['SifVersion'] == 65559:
            for _ in range(9):
                self.fp.readline()
        elif self.info['SifVersion'] == 65565:
            for _ in range(15):
                self.fp.readline()
            print(self.fp.readline())
        elif self.info['SifVersion'] > 65565:
            for _ in range(18):
                self.fp.readline()

        self.info['SifCalbVersion'] = int(_read_until_space(self.fp)) # 65539
        # additional skip for this version
        if self.info['SifCalbVersion'] == 65540:
            self.fp.readline()

        self.fp.readline() # 0x01 space NULL space 0x01 space NULL space 0x01 space NULL newline
        self.fp.readline() # 0 1 0 0 newline
        self.fp.readline() # 0 1 0 0 newline
        self.fp.readline() # 0 1 0 0 newline

        self.fp.readline() # 422 newline or 433 newline

        self.fp.readline() # 13 newline
        self.fp.readline() # 13 newline

        self.info['FrameAxis'] = _read_string(self.fp)
        self.info['DataType'] = _read_string(self.fp)
        self.info['ImageAxis'] = _read_string(self.fp)

        _read_until_space(self.fp) # 65541

        _read_until_space(self.fp) # x0? left? -> x0
        _read_until_space(self.fp) # x1? bottom? -> y1
        _read_until_space(self.fp) # y1? right? -> x1
        _read_until_space(self.fp) # y0? top? -> y0

        no_images = int(_read_until_space(self.fp))
        no_subimages = int(_read_until_space(self.fp))
        total_length = int(_read_until_space(self.fp))
        image_length = int(_read_until_space(self.fp))
        self.info['NumberOfFrames'] = no_images

        _read_until_space(self.fp) # 65538

        frame_area = self.fp.readline().strip().split()
        [x0,x1,y1,y0,xbin,ybin] = map(int,frame_area[:6]) # is order of x and y correct?
        width = int((1 + x1 - x0) / xbin)
        height = int((1 + y1 - y0) / ybin)
        #for frame in range(self.info['NumberOfFrames']):
        #     self.info['Frame_{:d}_Comment'.format(frame)] = _read_string(self.fp)

        self.mode = 'F'
        self.size = (int(width), int(height))

        self.tile = []
        offset = self.fp.tell() + 2
        for frame in range(self.info['NumberOfFrames']):
            self.tile.append(('raw', (0, 0) + self.size,
                              offset + frame * 4 * width * height,
                              ('F;32F', 0, 1)))

# --------------------------------------------------------------------
# Registry

Image.register_open("SIF", SifImageFile)
Image.register_extension("SIF", ".sif")
