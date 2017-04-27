import os
import sys
THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + '/../')

import numpy as np
import unittest
import PIL.Image
import plugin, sif_open


class test(unittest.TestCase):
    def test_open(self):
        data = PIL.Image.open(THIS_DIR + '/examples/image.sif')
        actual = np.asarray(data)
        expected, _ = sif_open.np_open(THIS_DIR + '/examples/image.sif')
        self.assertTrue(np.allclose(actual, expected))

if __name__ == '__main__':
     unittest.main()
