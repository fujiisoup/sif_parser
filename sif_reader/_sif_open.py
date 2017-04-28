from collections import OrderedDict

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

def _read_until(fp, terminator=' '):
    '''Read a space-delimited word.'''
    word = ''
    while True:
        c = _to_string(fp.read(1))
        if c == terminator or c == '\n':
            if len(word) > 0:
                break
        word += c
    return word

def _read_int(fp):
    return int(_read_until(fp, ' '))

def _read_float(fp):
    return float(_read_until(fp, ' '))

def _open(fp):
    """
    A helper function to read SIF file.

    Parameters
    -----------
    fp: File pointing to SIF file

    Returns
    -------
    tile: list
        A list of tuples, that contains the image location in the file.
    size: a tuple, (wdith, height)
    n_frames: integer
        number of frames
    info: dict
        Dictionary containing misc data.
    """
    info = OrderedDict()

    if _to_string(fp.read(36)) != _MAGIC:
        raise SyntaxError('not a SIF file')

    # What's this?
    fp.readline() # 65538 number_of_images?

    info['SifVersion'] = int(_read_until(fp, ' ')) # 65559

    # What's this?
    _read_until(fp, ' ') # 0
    _read_until(fp, ' ') # 0
    _read_until(fp, ' ') # 1

    info['ExperimentTime'] = _read_int(fp)
    info['DetectorTemperature'] = _read_float(fp)

    # What is this?
    _read_string(fp, 10) # blank

    # What is this?
    _read_until(fp, ' ') # 0

    info['ExposureTime'] = _read_float(fp)
    info['CycleTime'] = _read_float(fp)
    info['AccumulatedCycleTime'] = _read_float(fp)
    info['AccumulatedCycles'] = _read_int(fp)

    fp.read(1) # NULL
    fp.read(1) # space

    info['StackCycleTime'] = _read_float(fp)
    info['PixelReadoutTime'] = _read_float(fp)

    # What is this?
    _read_until(fp, ' ') # 0
    _read_until(fp, ' ') # 1
    info['GainDAC'] = _read_float(fp)

    # What is the rest of the line?
    _read_until(fp, '\n')

    info['DetectorType'] = _to_string(fp.readline())
    info['DetectorDimensions'] = (_read_int(fp), _read_int(fp))
    info['OriginalFilename'] = _read_string(fp)

    # What is this?
    fp.read(2) # space newline
    _read_until(fp, ' ') # 65538

    # What is this?
    _read_string(fp) # Is this some type of experiment comment?
    fp.read(1) # newline
    _read_int(fp) # 65538
    fp.read(8) # 0x01 space 0x02 space 0x03 space 0x00 space
    info['ShutterTime'] = (_read_float(fp), _read_float(fp)) # ends in newline

    if (65548 <= info['SifVersion'] &
            info['SifVersion'] <= 65557):
        for _ in range(2):
            fp.readline()
    elif info['SifVersion'] == 65558:
        for _ in range(5):
            fp.readline()
    elif info['SifVersion'] == 65559:
        for _ in range(9):
            fp.readline()
    elif info['SifVersion'] == 65565:
        for _ in range(15):
            fp.readline()
    elif info['SifVersion'] > 65565:
        for _ in range(18):
            fp.readline()

    info['SifCalbVersion'] = int(_read_until(fp, ' ')) # 65539
    # additional skip for this version
    if info['SifCalbVersion'] == 65540:
        fp.readline()

    fp.readline() # 0x01 space NULL space 0x01 space NULL space 0x01 space NULL newline
    fp.readline() # 0 1 0 0 newline
    fp.readline() # 0 1 0 0 newline
    fp.readline() # 0 1 0 0 newline

    fp.readline() # 422 newline or 433 newline

    fp.readline() # 13 newline
    fp.readline() # 13 newline

    info['FrameAxis'] = _read_string(fp)
    info['DataType'] = _read_string(fp)
    info['ImageAxis'] = _read_string(fp)

    _read_until(fp, ' ') # 65541

    _read_until(fp, ' ') # x0? left? -> x0
    _read_until(fp, ' ') # x1? bottom? -> y1
    _read_until(fp, ' ') # y1? right? -> x1
    _read_until(fp, ' ') # y0? top? -> y0

    no_images = int(_read_until(fp, ' '))
    no_subimages = int(_read_until(fp, ' '))
    total_length = int(_read_until(fp, ' '))
    image_length = int(_read_until(fp, ' '))
    info['NumberOfFrames'] = no_images

    for i in range(no_subimages):
        # read subimage information
        _read_until(fp, ' ') # 65538

        frame_area = fp.readline().strip().split()
        x0, y1, x1, y0, ybin, xbin = map(int,frame_area[:6])
        width = int((1 + x1 - x0) / xbin)
        height = int((1 + y1 - y0) / ybin)
    size = (int(width), int(height) * no_subimages)
    tile = []

    for f in range(no_images):
        info['timestamp_of_{0:d}'.format(f)] = int(fp.readline())

    offset = fp.tell()
    try: # remove extra 0 if it exits.
        if int(fp.readline()) == 0:
            offset = fp.tell()
    except:
        fp.seek(offset)

    for f in range(no_images):
        tile.append(("raw", (0, 0) + size,
                     offset + f * width * height * 4,
                     ('F;32F', 0, 1)))

    return tile, size, no_images, info
