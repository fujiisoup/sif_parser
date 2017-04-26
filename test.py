import numpy as np
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
        data.show()

    def test2(self):
        data = PIL.Image.open('examples/134063.SIF')
        info = data.info
        array = np.asarray(data)
        print(data.tell())
        print(array.shape)
        self.assertTrue(list(array.shape) == [1024, 1])
        data.seek(1)
        array = np.asarray(data)
        self.assertTrue(list(array.shape) == [1024, 1])

if __name__ == '__main__':
     unittest.main()
