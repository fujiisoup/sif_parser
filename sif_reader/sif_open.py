import numpy as np
from ._sif_open import _open

def np_open(sif_file):
    """
    Open sif_file and return as np.array.
    """
    if isinstance(sif_file, str):
        f = open(sif_file, 'rb')
    else: # file instance
        f = sif_file

    tile, size, no_images, info = _open(f)
    # allocate np.array
    data = np.ndarray((no_images, size[0], size[1]), dtype=np.float32)
    for i, tile1 in enumerate(tile):
        f.seek(tile1[2])  # offset
        data[i] = np.fromfile(f, count=size[0]*size[1],
                              dtype='<f').reshape(*size)

    # close file if filename pass
    if isinstance(sif_file, str):
        f.close()

    return data, info

# --- xarray open ---
try:
    import xarray as xr

    def xr_open(sif_file):
        """
        Read file and set into xr.DataArray.
        """
        data, info = np_open(sif_file)
        # extract time stamps
        time = np.ndarray(len(data), dtype=np.float)
        for f in range(len(data)):
            time[f] = info['timestamp_of_{0:d}'.format(f)] * 1.0e-6  # unit [s]
            info['timestamp_of_{0:d}'.format(f)]

        return xr.DataArray(data, dims=['time', 'width', 'height'],
                            coords={'time': time}, attrs=info)

except ImportError:
    pass
