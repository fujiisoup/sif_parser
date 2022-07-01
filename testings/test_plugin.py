import os
THIS_DIR = os.path.dirname(__file__)

import numpy as np
import unittest
import PIL.Image
from sif_parser import plugin, np_open


class test(unittest.TestCase):
    def _test_open(self):
        data = PIL.Image.open(THIS_DIR + '/examples/image.sif')
        actual = np.asarray(data)
        expected, _ = np_open(THIS_DIR + '/examples/image.sif')
        self.assertTrue(np.allclose(actual, expected))


if __name__ == '__main__':
    unittest.main()
