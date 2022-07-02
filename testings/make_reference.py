"""
Make a reference data for testing
"""
import os
import sys
THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + '/../sif_parser/')

# data directories that will be tested
PUBLIC_DATA_DIR = THIS_DIR + '/public_testdata/'
PRIVATE_DATA_DIR = THIS_DIR + '/sif_parser_testdata/'

import numpy as np
import matplotlib.pyplot as plt
import sif_parser


files = [PUBLIC_DATA_DIR + f for f in  os.listdir(PUBLIC_DATA_DIR) if f[-4:].lower() == '.sif']
files += [PRIVATE_DATA_DIR + f for f in os.listdir(PRIVATE_DATA_DIR) if f[-4:].lower() == '.sif']

for file in files:
    with open(file, 'rb') as f:
        da = sif_parser.xr_open(f)
    np.savez(file[:-4] + '.npz', da.values)
    # save image
    da.isel(Time=0).plot()
    plt.savefig(file[:-4] + '.png')
    plt.clf()
