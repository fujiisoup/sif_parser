import os
import sys
THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + '/../sif_reader/')

# data directories that will be tested
DATA_DIR = THIS_DIR + '/sif_reader_testdata/'

import numpy as np
import os
import unittest
import sif_reader
import _sif_open

class test(unittest.TestCase):
    def test_multiple_open(self):
        filenames = os.listdir(DATA_DIR)
        if os.path.exists(DATA_DIR):
            for filename in filenames:
                if filename[-4:] == '.sif' or filename[-4:] == '.SIF':
                    print('reading ' + filename)
                    with open(DATA_DIR + filename, 'rb') as f:
                        data, info = sif_reader.np_open(f)
                    self.assertTrue(np.sum(np.isnan(data)) == 0)

    def test_open(self):
        with open(THIS_DIR + '/examples/image.sif', 'rb') as f:
            tile, size, n_frames, info = _sif_open._open(f)

        self.assertTrue(len(tile) == 1)
        self.assertTrue(tile[0][1] == (0, 0, 512, 512))
        self.assertTrue(n_frames == 1)

    def test_np_open(self):
        with open(THIS_DIR + '/examples/image.sif', 'rb') as f:
            data, info = sif_reader.np_open(f)

        self.assertTrue(list(data.shape) == [1, 512, 512])
        self.assertTrue(np.sum(np.isnan(data)) == 0)

try:
    import xarray as xr

    class Test_xr_open(unittest.TestCase):
        def test_xr_open2(self):
            da = sif_reader.xr_open(THIS_DIR + '/examples/image.sif')
            self.assertTrue(np.sum(np.isnan(da)) == 0)
            self.assertTrue('timestamp_of_0' not in da.attrs.keys())
            self.assertTrue('Time' in da.coords)
            self.assertTrue('width' in da.dims)
            self.assertTrue('height' in da.dims)

except ImportError:
    pass


if __name__ == '__main__':
     unittest.main()
