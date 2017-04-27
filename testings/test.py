import numpy as np
import matplotlib.pyplot as plt
import PIL
import SifImagePlugin
import unittest

class test(unittest.TestCase):
    def test_load(self):
        data = PIL.Image.open('examples/image.sif')
        data.load()
        array = np.asarray(data)
        self.assertTrue(list(array.shape) == [512, 512])
        print(np.max(array))
        plt.imshow(data)
        
    def test2(self):
        data = PIL.Image.open('examples/134063.SIF')
        info = data.info
        array = np.asarray(data)
        self.assertTrue(list(array.shape) == [1024, 1])
        self.assertTrue(data.n_frames == 2000)
        data.seek(1)
        data.load()
        array = np.asarray(data)
        self.assertTrue(list(array.shape) == [1024, 1])

if __name__ == '__main__':
     unittest.main()
