import PIL
import SifImagePlugin
import unittest

class test(unittest.TestCase):
    def test_load(self):
        data = PIL.Image.open('image.sif')
        data.load()
        print(data.info)

if __name__ == '__main__':
     unittest.main()
