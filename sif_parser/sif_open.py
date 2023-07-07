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

    Parameters
    ----------
    spool_dir: 
        directory path containing the spooling files. 
        Must contain at least one "sifx_file", one "ini_file" and 
        one or more "spooled_file(s)":
        
    ignore_missing: 
        True if ignore missing or corrupted *.dat files
    
    lazy: either of None | 'memmap' | 'dask'
        None: load all the data into the memory
        'memmap': returns np.memmap pointing on the disk
        'dask': returns dask.Array that consists of np.memmap
            This requires dask installed into the computer. *Not yet implemented*
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
            raise ValueError(f"Problem handeling the 'ini' file. Probably the file is corrupted, keys are missing or at the wrong place. Check your 'ini' file")
    else:
        raise ValueError(f"Problem handeling the 'ini' file. The File seems to be incomplete or truncated. Check your 'ini' file")

# Checking for supported pixel encoding
    allowed_encodings = ['Mono16', 'Mono32', 'Mono12Packed']
    if ini_info['PixelEncoding'] not in allowed_encodings:
        raise ValueError(f"Unknown pixel encoding found with value: '{ini_info['PixelEncoding']}. Allowed pixel encodings are: {allowed_encodings}.'")
    
    # read only metadata (ignoring expected warning on missing data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _ , info = np_open(sifx_file[0], ignore_corrupt=True)

    # get the expected shape of the image from metadata
    x, y = info["DetectorDimensions"]
    t = info["NumberOfFrames"]

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
  

    if ini_info['PixelEncoding'] != allowed_encodings[2]:

        if ini_info['PixelEncoding'] == allowed_encodings[0]:
            datatype = np.uint16
            n_bits = 2
        elif ini_info['PixelEncoding'] == allowed_encodings[1]:        
            datatype = np.uint32
            n_bits = 4    
        # shape of ini file
        x_, y_ =  int( int(ini_info['AOIStride']) / n_bits ), int(ini_info['AOIHeight'])                
        # create np array with the given info     
        data = np.empty( [t, y_, x_], datatype ) 

        for frame in range(t):
            data[frame, ...] = np.fromfile(dat_files_list[frame], 
            offset=0, 
            dtype=datatype,
            count= y_ * x_).reshape(y_, x_)
        # account for the extra padding to trim if present
        if x != x_:
            end_padding =  x_ - x
            data = data[:, :, :-end_padding]
    else:
        def read_uint12(data_chunk):
            data = np.frombuffer(data_chunk, dtype=np.uint8)
            fst_uint8, mid_uint8, lst_uint8 = np.reshape(data, (data.shape[0] // 3, 3)).astype(np.uint16).T
            fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
            snd_uint12 = (lst_uint8 << 4) + (np.bitwise_and(15, mid_uint8))
            return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

        x, x_, y = int(ini_info['AOIWidth']), int(ini_info['AOIStride']), int(ini_info['AOIHeight'])
        image_mono12 = []
        for frame in range(t):
            with open(dat_files_list[frame], 'rb') as f:
                dat = f.read()
            for i in range(y):
                image_mono12.append(read_uint12(dat[x_ * i: x_ * i + x * 3 // 2 ]))
        
        data = np.stack(image_mono12, axis = 0).reshape((t, y, x))  


    return data, info

