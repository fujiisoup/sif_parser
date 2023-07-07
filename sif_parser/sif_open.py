import warnings
import numpy as np
from collections import OrderedDict
from ._sif_open import _open
from .utils import extract_calibration
import glob


def np_open(sif_file, ignore_corrupt=False, lazy=None):
    """
    Open sif_file and return as np.array.

    Parameters
    ----------
    sif_file: 
        path to the file
    ignore_corrupt: 
        True if ignore the corrupted frames.
    lazy: either of None | 'memmap' | 'dask'
        None: load all the data into the memory
        'memmap': returns np.memmap pointing on the disk
        'dask': returns dask.Array that consists of np.memmap
            This requires dask installed into the computer.
    """
    will_close = False
    try:
        f = sif_file
        tile, size, no_images, info = _open(f)
    except AttributeError:
        f = open(sif_file,'rb')
        tile, size, no_images, info = _open(f)
        will_close = True

    # allocate np.array
    if lazy == 'dask':
        try:
            import dask.array as da
        except ImportError:
            raise ImportError(
                "Install dask to use lazy='dask'"
            )

    if lazy == 'memmap':
        # make sure the data is contiguous
        sizes = [tile[i + 1][2] - tile[i][2] for i in range(len(tile) - 1)]
        if not np.all(size[0] * size[1] * np.dtype('<f').itemsize == np.array(sizes)):
            raise ValueError(
                "The data is not contiguous. Use lazy='dask' instead."
            )

    if lazy is None:
        data = np.ndarray((no_images, size[1], size[0]), dtype=np.float32)
    elif lazy == 'memmap':
        data = np.memmap(
            sif_file, '<f', mode='r', offset=tile[0][2], shape=(len(tile), size[1], size[0]), 
            order='C'
        )
    elif lazy == 'dask':
        data = [None for _ in range(len(tile))]

    for i, tile1 in enumerate(tile):
        f.seek(tile1[2])  # offset
        try:
            if lazy is None:
                data[i] = np.fromfile(f, count=size[0]*size[1],dtype='<f').reshape(size[1],size[0])
            elif lazy == 'dask':
                data[i] = da.from_array(np.memmap(
                    f, dtype='<f', mode='r', offset=tile1[2], 
                    shape=(size[1], size[0]), order='C'
                ), chunks=(-1, -1))

        except ValueError:
            data = data[:i]
            if not ignore_corrupt:
                raise ValueError(
                    'The file might be corrupt. Number of files should be {} '
                    'according to the header, but only {} is found in the file.'
                    'Use "ignore_corrupt=True" keyword argument to ignore.'.format(
                        no_images, len(data)
                    )
                )
            else:
                warnings.warn(
                    'The file might be corrupt. Number of files should be {} '
                    'according to the header, but only {} is found in the file.'.format(
                        no_images, len(data)
                    )
                )

    if will_close:
        f.close()
        
    if lazy == 'dask':
        data = da.stack(data, axis=0)        
    return data, info

# --- xarray open ---
def xr_open(sif_file, ignore_corrupt=False, lazy=None):
    """
    Read file and set into xr.DataArray.
    
    Parameters
    ----------
    sif_file: 
        path to the file
    ignore_corrupt: 
        True if ignore the corrupted frames.
    lazy: either of None | 'memmap' | 'dask'
        None: load all the data into the memory
        'memmap': returns np.memmap pointing on the disk
        'dask': returns dask.Array that consists of np.memmap
            This requires dask installed into the computer.
    """
    try:
        import xarray as xr
    except ImportError:
        raise ImportError(
            "xarray needs to be installed to use xr_open."
        )

    data, info = np_open(sif_file, ignore_corrupt=ignore_corrupt, lazy=lazy)
    # make Variable first to avoid converting to np.array
    data = xr.core.variable.Variable(['Time', 'height', 'width'], data, fastpath=True)
    
    # coordinates
    coords = OrderedDict()
    # extract time stamps
    time = np.ndarray(len(data), dtype=float)
    for f in range(len(data)):
        time[f] = info['timestamp_of_{0:d}'.format(f)] * 1.0e-6  # unit [s]
    coords['Time'] = (('Time', ), time, {'Unit': 's'})

    # calibration data
    x_calibration = extract_calibration(info)
    if x_calibration is not None:
        if x_calibration.ndim == 2 and x_calibration.shape == (data.shape[0], data.shape[2]):
            coords['calibration'] = (('Time', 'width'), x_calibration)
        elif x_calibration.shape == x_calibration.shape == (data.shape[2], ):
            coords['calibration'] = (('width'), x_calibration)

    new_info = OrderedDict()
    unused_keys = ['Calibration_data', 'timestamp_of_', 'tile']
    for key in list(info.keys()):
        if all(k not in key for k in unused_keys):
            new_info[key] = info[key]
            # remove time stamps from attrs
            if type(new_info[key]) == bytes:
                new_info[key] = new_info[key].decode('utf-8')
    

    return xr.DataArray(data, dims=['Time', 'height', 'width'],
                        coords=coords, attrs=new_info)

def np_spool_open(spool_dir, ignore_missing=False, lazy=None):
    """
    Read from a directory the binary files and metadata generates via spooling and return a np.array. 

    Spooling acquisition save your data directly o disk when reading from your camera.
    When spooling acquisition is enabled, a directory is created in your PC
    and the data is written directly on the hard disk as it is being acquired.

    Spooling acquisition normally generates the following files by default:

     - "sifx_file": 1 file with the extension "*.sifx". This is the header of 
        the file containing the metadata.
     - "ini_file": 1 file with the extension "*.ini". This file contain information on the 
        image format such as number of pixels by row (AOIWidth) number of rows and (AOIHeight) 
        and padding bytes (AOIStride) (See the Andor SDK Manuel for more details).
     - "spooled_file(s)": file or set of files with the extension "*spool.dat" 
        containing the actual image data as binary files.
    
    Parameters
    ----------
    spool_dir: 
        path to the directory containing the spooling files. 
        Must contain at least one "sifx_file", one "ini_file" and 
        one or more "spooled_file(s)":
        
    ignore_missing: 
        True if ignore missing binary files.
    
    lazy: either of None | 'memmap' | 'dask'
        None: load all the data into the memory
        'memmap': returns np.memmap pointing on the disk
        'dask': returns dask.Array that consists of np.memmap
            This requires dask installed into the computer.
    """
    dat_files_list = sorted(glob.glob(spool_dir + "/*spool.dat"))
    ini_file = glob.glob(spool_dir + "/*.ini" )
    sifx_file = glob.glob(spool_dir + "/*.sifx")

    if len(dat_files_list) < 1:
        raise ValueError('Not Binary file(s) with extension {} found in the directory provided {} '.format(
            "*spool.dat", spool_dir))
    if len(ini_file) < 1:
        raise ValueError('Not "ini_file" file with extension {} found in the directory provided {} '.format(
            "*.ini" , spool_dir))
    if len(sifx_file) < 1:
        raise ValueError('Not "sifx_file" file with extension {} found in the directory provided {} '.format(
            "*.sifx", spool_dir))


# Checking for missing or corrupted ini file. File must be lenght >=10 and contain the spected keys, vals in the right order.
    with open(ini_file[0], "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) >= 10:
        keys, vals = zip(*[lines[i][:-1].replace(" ", "").split("=") for i in [*range(1, 6), 9]])
        if (keys[0] == 'AOIHeight' and  keys[1] == 'AOIWidth' and keys[2] =='AOIStride' and keys[3] =='PixelEncoding' and keys[4] =='ImageSizeBytes' and keys[5] == 'ImagesPerFile'):
            ini_info = OrderedDict(zip(keys, vals))  
        else:
            raise ValueError(f"Problem handeling the 'ini' file. Probably the file is corrupted, keys are missing ir in the wrong place. Check your 'ini' file")
    else:
        raise ValueError(f"Problem handeling the 'ini' file. The File seems to be incomplete or truncated. Check your 'ini' file")


    if ini_info['PixelEncoding'] == 'Mono16':
        print("pixel endcoding is 'Mono16'")
        datatype = np.uint16
    if ini_info['PixelEncoding'] == 'Mono12Packed':
        print("pixel endcoding is 'Mono12Packed'")
        # datatype = np.uint16
    if ini_info['PixelEncoding'] == 'Mono32':
        print("pixel endcoding is 'Mono32'")
        datatype = np.uint32
    

    else:
        raise ValueError(f"We found different data format than Mono16 with value: {ini_info['PixelEncoding']} ")
    
    # read only metadata (ignoring expected warning on missing data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _ , metadata = np_open(sifx_file[0], ignore_corrupt=True)

    # get the actual shape of the image from metadata
    x, y = metadata["DetectorDimensions"]
    t = metadata["NumberOfFrames"]

    if len(dat_files_list) != t:
        if not ignore_missing:
            raise ValueError('The spooling acquisition might be corrupt. Number of files should be {} '
                        'according to the header, but only {} binary files were found in the directory.'.format(
                            t, len(dat_files_list)))
        else:
            warnings.warn('The spooling acquisition might be corrupt. Number of files should be {} '
                        'according to the header, but only {} binary files were found in the directory.'.format(
                            t, len(dat_files_list)))
            t = len(dat_files_list)

    # shape of ini file
    x_, y_ =  int( int(ini_info['AOIStride']) / 2 ), int(ini_info['AOIHeight'])
   # account for the extra padding to trim it later
    
    
    # create np array with the given info     
    data = np.empty( [t, y_, x_] ) 

    for frame in range(t):
        data[frame, ...] = np.fromfile(dat_files_list[frame], 
                                       offset=0, 
                                       dtype=datatype, 
                                       count= y_ * x_).reshape(y_, x_)
    if x != x_:
        end_padding =  x_ - x
        data = data[:, :, :-end_padding]


    return data, metadata

