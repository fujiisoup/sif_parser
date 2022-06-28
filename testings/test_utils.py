from collections import OrderedDict
import numpy as np
import os
import sys
THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + '/../sif_reader/')

# data directories that will be tested
DATA_DIR = THIS_DIR + '/sif_reader_testdata/'

import PIL.Image
import unittest
from sif_reader import utils


class TestExtract(unittest.TestCase):
    def test_calibration(self):
        info = OrderedDict()
        info['DetectorDimensions'] = (1024, 100)
        info['Calibration_data'] = [0.1, 0.2, 0.3, 0.4]

        actual = utils.extract_calibration(info)
        expected = np.poly1d(np.flipud(info['Calibration_data']))(
                                    np.arange(1, 1025))
        self.assertTrue(np.allclose(actual, expected))

    def test_calibration_multi_frames(self):
        info = OrderedDict()
        info['DetectorDimensions'] = (1024, 100)
        info['NumberOfFrames'] = 3
        info['Calibration_data'] = [0.1, 0.2, 0.3, 0.4]
        info['Calibration_data_for_frame_1'] = [0.11, 0.21, 0.31, 0.41]
        info['Calibration_data_for_frame_2'] = [0.12, 0.22, 0.32, 0.42]
        info['Calibration_data_for_frame_3'] = [0.13, 0.23, 0.33, 0.43]

        actual = utils.extract_calibration(info)
        for f in range(3):
            key = 'Calibration_data_for_frame_{:d}'.format(f+1)
            expected = np.poly1d(np.flipud(info[key]))(np.arange(1, 1025))
            self.assertTrue(np.allclose(actual[f], expected))


if __name__ == '__main__':
     unittest.main()
