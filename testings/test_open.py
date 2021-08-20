import os
import sys
THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + '/../sif_reader/')

# data directories that will be tested
DATA_DIR = THIS_DIR + '/sif_reader_testdata/'
PUBLIC_DATA_DIR = THIS_DIR + '/public_testdata/'

import PIL.Image
import numpy as np
import os
import pytest
import unittest
import sif_reader
import _sif_open, utils


filenames = []
for d in [DATA_DIR, PUBLIC_DATA_DIR]:
    if os.path.exists(d):
        files = os.listdir(d)
        filenames += [d + f for f in files if f[-4:] in ['.sif', '.SIF']]

@pytest.mark.parametrize('filename', filenames)
def test_open(filename):
    with open(filename, 'rb') as f:
        data, info = sif_reader.np_open(f)
    assert np.sum(np.isnan(data)) == 0

    # open reference data if exists
    reffile = filename[:-4] + '.npz'
    if os.path.exists(reffile):
        ref = np.load(reffile)
        ref = ref[list(ref.keys())[0]]
        assert np.allclose(ref, data)


def test_one_image():
    with open(PUBLIC_DATA_DIR + 'image.sif', 'rb') as f:
        tile, size, n_frames, info = _sif_open._open(f)

    assert len(tile) == 1
    assert tile[0][1] == (0, 0, 512, 512)
    assert n_frames == 1


class TestCalibration(unittest.TestCase):
    """
    Test to make sure the calibration data is certainly read.
    """
    def setUp(self):
        self.filenames = []
        self.answer_files = []
        DATA_DIR2 = THIS_DIR + '/examples_with_calibration/'
        filenames = os.listdir(DATA_DIR2)
        for filename in filenames:
            if filename[-4:] == '.sif' or filename[-4:] == '.SIF':
                self.filenames.append(DATA_DIR2 + filename)
                self.answer_files.append(DATA_DIR2 + filename[:-4] + '.asc')

    def test_np_open(self):
        def read_lines(f):
            lines = []
            x = []
            for i, line in enumerate(f):
                try:
                    stripped = line.split()
                    array = np.array([float(v) for v in stripped])
                    if i == 0 or array.shape == lines[-1].shape:
                        lines.append(array)
                        x.append(array[0])
                except Exception:
                    break
            return np.array(x), np.array(lines)[:, 1:]

        for filename, answer_file in zip(self.filenames, self.answer_files):
            with open(filename, 'rb') as f:
                actual, info = sif_reader.np_open(f)
            with open(answer_file, 'rb') as f:
                expected_x, expected = read_lines(f)
                expected = expected.reshape(actual.shape[0],
                                            actual.shape[2],
                                            actual.shape[1])
                expected = np.moveaxis(expected, 1, -1)
            self.assertTrue(np.allclose(actual, expected))

            actual_x = utils.extract_calibration(info)
            if actual_x.ndim == 1:
                self.assertTrue(np.allclose(actual_x, expected_x))

            # test with xarray
            try:
                import xarray as xr
                # make sure it can be opened
                actual_xr = sif_reader.xr_open(filename)

            except ImportError:
                pass


try:
    import xarray as xr

    class Test_xr_open(unittest.TestCase):
        def test_xr_open2(self):
            da = sif_reader.xr_open(PUBLIC_DATA_DIR + 'image.sif')
            self.assertTrue(np.sum(np.isnan(da)) == 0)
            self.assertTrue('timestamp_of_0' not in da.attrs.keys())
            self.assertTrue('Time' in da.coords)
            self.assertTrue('width' in da.dims)
            self.assertTrue('height' in da.dims)

        def test_multiple_open(self):
            filenames = []
            for d in [DATA_DIR, PUBLIC_DATA_DIR]:
                if os.path.exists(d):
                    files = os.listdir(d)
                    filenames += [d + f for f in files if f[-4:] in ['.sif', '.SIF']]

            for filename in filenames:
                print('reading ' + filename)
                with open(filename, 'rb') as f:
                    data = sif_reader.xr_open(f)


except ImportError:
    pass


if __name__ == '__main__':
     unittest.main()
