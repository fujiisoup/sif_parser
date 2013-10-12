from PIL import Image, ImageFile

# Read Andor Technology Multi-Channel files with PIL.
# Based on Marcel Leutenegger's MATLAB script.

_MAGIC = 'Andor Technology Multi-Channel File\n'

# --------------------------------------------------------------------
# SIF reader

def _read_string(fp, length = None):
    '''Read a string of the given length. If no length is provided, the
    length is read from the file.'''
    if length is None:
        length = int(fp.readline())
    return fp.read(length)

def _read_until_space(fp):
    '''Read a space-delimited word.'''
    word = ''
    while True:
        c = fp.read(1)
        if c == ' ' or c == '\n':
            break
        word += c
    return word

def _read_int(fp):
    return int(_read_until_space(fp))

def _read_float(fp):
    return float(_read_until_space(fp))

class SifImageFile(ImageFile.ImageFile):
    format = "SIF"
    format_description = "Andor Technology Multi-Channel File"

    def _open(self):
        if self.fp.read(36) != _MAGIC:
            raise SyntaxError('not a SIF file')

        # What's this?
        self.fp.readline() # 65538 number_of_images?

        # What's this?
        _read_until_space(self.fp) # 65559
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

        self.info['DetectorType'] = _read_string(self.fp)

        # What is this?
        self.fp.read(3) # space newline space

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

        _read_until_space(self.fp) # 65540
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 500
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 1200
        _read_until_space(self.fp) # 1200 # ends in newline

        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 10 # ends in newline

        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        self.fp.read(1) # space
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 10 # ends in newline

        _read_until_space(self.fp) # 0
        _read_string(self.fp, 6) # SR303i
        self.fp.read(1) # newline

        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 10 # ends in newline

        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 10 # ends in newline

        _read_until_space(self.fp) # 0
        _read_until_space(self.fp) # 0
        self.fp.read(1) # newline

        _read_until_space(self.fp) # 65536
        _read_until_space(self.fp) # 1
        _read_until_space(self.fp) # 500
        _read_until_space(self.fp) # 200 # ends in newline

        _read_until_space(self.fp) # 5
        self.fp.readline() # SR163

        _read_until_space(self.fp) # 65539
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

        self.info['NumberOfFrames'] = 1 - _read_int(self.fp) + _read_int(self.fp);

        self.fp.readline() # 1048576 space 1048576 newline

        _read_until_space(self.fp) # 65538

        frame_area = self.fp.readline().strip().split()
        [x0,x1,y1,y0,ybin,xbin] = map(int,frame_area[:6]) # is order of x and y correct?
        width = (1 + x1 - x0) / xbin
        height = (1 + y1 - y0) / ybin
        for frame in range(self.info['NumberOfFrames']):
             self.info['Frame_{:d}_Comment'] = _read_string(self.fp)

        self.mode = 'F'
        self.size = (width, height)

        self.tile = []
        offset = self.fp.tell() + 2
        for frame in range(self.info['NumberOfFrames']):
            self.tile.append(('raw', (0,0) + self.size , offset + frame * 4 * width * height, ('F;32F', 0, 1)))


# --------------------------------------------------------------------
# Registry

Image.register_open("SIF", SifImageFile)
Image.register_extension("SIF", ".sif")
