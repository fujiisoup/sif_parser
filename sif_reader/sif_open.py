import numpy as np
from ._sif_open import _open

def np_open(sif_file):
    """
    Open sif_file and return as np.array.
    """    
    try:
        f = sif_file
        tile, size, no_images, info = _open(f)
    except AttributeError:
        f = open(sif_file,'rb')
        tile, size, no_images, info = _open(f)
    # allocate np.array
    data = np.ndarray((no_images, size[1], size[0]), dtype=np.float32)
    for i, tile1 in enumerate(tile):
        f.seek(tile1[2])  # offset
        data[i] = np.fromfile(f, count=size[0]*size[1],dtype='<f').reshape(size[1],size[0])
        
    try:
        f.close()
    finally:
        pass

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
            del info['timestamp_of_{0:d}'.format(f)]

        return xr.DataArray(data, dims=['Time', 'width', 'height'],
                            coords={'Time': time}, attrs=info)

except ImportError:
    pass
