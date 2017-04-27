import os
import sys
THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + '/../')

import numpy as np
import unittest
import _sif_open
import sif_open

class test(unittest.TestCase):
    def test_open(self):
        with open(THIS_DIR + '/examples/image.sif', 'rb') as f:
            tile, size, n_frames, info = _sif_open._open(f)

        self.assertTrue(len(tile) == 1)
        self.assertTrue(tile[0][1] == (0, 0, 512, 512))
        self.assertTrue(n_frames == 1)

    def test_np_open(self):
        with open(THIS_DIR + '/examples/image.sif', 'rb') as f:
            data, info = sif_open.np_open(f)

        self.assertTrue(list(data.shape) == [1, 512, 512])
        self.assertTrue(np.sum(np.isnan(data)) == 0)

    def test_np_open2(self):
        with open(THIS_DIR + '/examples/134063.SIF', 'rb') as f:
            data, info = sif_open.np_open(f)

        self.assertTrue(list(data.shape) == [2000, 1, 1024])
        self.assertTrue(np.sum(np.isnan(data)) == 0)

try:
    import xarray as xr

    class Test_xr_open(unittest.TestCase):
        def test_xr_open2(self):
            da = sif_open.xr_open(THIS_DIR + '/examples/134063.SIF')

            self.assertTrue(list(da.shape) == [2000, 1, 1024])
            self.assertTrue(np.sum(np.isnan(da)) == 0)
            # The first frame ranges 0 ~ 1000
            self.assertTrue((da.isel(time=0) < 1000.0).all())
            self.assertTrue((da.isel(time=0) > 0.0).all())
            # Known time axis
            self.assertTrue(np.allclose(da['time'], np.arange(2000) * 0.005))

except ImportError:
    pass

if __name__ == '__main__':
     unittest.main()
