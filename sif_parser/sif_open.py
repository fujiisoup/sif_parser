import warnings
import numpy as np
from collections import OrderedDict
from ._sif_open import _open
from .utils import extract_calibration


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
    lazy: either of None | 'dask'
        None: load all the data into the memory
        'dask': returns dask.Array that consists of np.memmap
            This requires dask installed into the computer.
    """
    try:
        import xarray as xr
    except ImportError:
        raise ImportError(
            "xarray needs to be installed to use xr_open."
        )

    if lazy == 'memmap':
        raise ValueError(
            "Memmap is not supported for `xr_open`.Use `lazy='dask'` instead.")
    data, info = np_open(sif_file, ignore_corrupt=ignore_corrupt, lazy=lazy)
    # coordinates
    coords = OrderedDict()
    # extract time stamps
    time = np.ndarray(len(data), dtype=np.float)
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

