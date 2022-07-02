import warnings
import numpy as np
from collections import OrderedDict
from ._sif_open import _open
from .utils import extract_calibration


def np_open(sif_file, ignore_corrupt=False):
    """
    Open sif_file and return as np.array.

    Parameters
    ----------
    sif_file: 
    ignore_corrupt
    """
    will_close = False
    try:
        f = sif_file
        tile, size, no_images, info = _open(f)
        will_close = True
    except AttributeError:
        f = open(sif_file,'rb')
        tile, size, no_images, info = _open(f)
    # allocate np.array
    data = np.ndarray((no_images, size[1], size[0]), dtype=np.float32)
    for i, tile1 in enumerate(tile):
        f.seek(tile1[2])  # offset
        try:
            data[i] = np.fromfile(f, count=size[0]*size[1],dtype='<f').reshape(size[1],size[0])
        except ValueError:
            if not ignore_corrupt:
                raise ValueError(
                    'The file might be corrupt. Number of files should be {} '
                    'according to the header, but only {} is found in the file.'.format(
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

    return data, info

# --- xarray open ---
def xr_open(sif_file):
    """
    Read file and set into xr.DataArray.
    """
    try:
        import xarray as xr
    except ImportError:
        raise ImportError(
            "xarray needs to be installed to use xr_open."
        )

    data, info = np_open(sif_file)
    # coordinates
    coords = OrderedDict()
    # extract time stamps
    time = np.ndarray(len(data), dtype=np.float)
    for f in range(len(data)):
        time[f] = info['timestamp_of_{0:d}'.format(f)] * 1.0e-6  # unit [s]
        del info['timestamp_of_{0:d}'.format(f)]
    coords['Time'] = (('Time', ), time, {'Unit': 's'})

    # calibration data
    x_calibration = extract_calibration(info)
    if x_calibration is not None:
        if x_calibration.ndim == 2 and x_calibration.shape == (data.shape[0], data.shape[2]):
            coords['calibration'] = (('Time', 'width'), x_calibration)
        elif x_calibration.shape == x_calibration.shape == (data.shape[2], ):
            coords['calibration'] = (('width'), x_calibration)

    new_info = OrderedDict()
    for key in info:
        if 'Calibration_data' not in key:
            new_info[key] = info[key]

    return xr.DataArray(data, dims=['Time', 'height', 'width'],
                        coords=coords, attrs=new_info)

