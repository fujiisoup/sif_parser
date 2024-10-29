import typing
import numpy as np
import os

from . import sif_open as sif


def extract_calibration(info):
    """
    Extract calibration data from info.

    Parameters
    ----------
    info: OrderedDict
        OrderedDict from np_open

    Returns
    -------
    calibration:
        np.ndarray.
        1d array sized [width] if only 1 calibration is found.
        2d array sized [NumberOfFrames x width] if multiple calibration is
            found.
        None if no calibration is found
    """
    width = info['ImageLength'] 
    # multiple calibration data is stored
    if 'Calibration_data_for_frame_1' in info:
        calibration = np.ndarray((info['NumberOfFrames'], width))
        for f in range(len(calibration)):
            key = 'Calibration_data_for_frame_{:d}'.format(f + 1)
            flip_coef = np.flipud(info[key])
            calibration[f] = np.poly1d(flip_coef)(np.arange(1, width + 1))
        return calibration

    elif 'Calibration_data' in info:
        flip_coef = np.flipud(info['Calibration_data'])
        return np.poly1d(flip_coef)(np.arange(1, width + 1))
    else:
        return None


def parse(file: str) -> typing.Tuple[np.ndarray, typing.Dict]:
    """
    Parse a .sif file.

    :param file: Path to a `.sif` file.
    :returns tuple[numpy.ndarray, OrderedDict]: Tuple of (data, info) where
        `data` is an (channels x 2) array with the first element of each row
        being the wavelength bin and the second being the counts.
        `info` is an OrderedDict of information about the measurement.
    """
    data, info = sif.np_open(file)
    wavelengths = extract_calibration(info)

    # @todo: `data.flatten()` may not be compatible with
    #   multiple images or 2D images.
    df = np.column_stack((wavelengths, data.flatten()))
    return (df, info)

def ordered_dat_files(input_string):
    """
    This helper function sort the list of .dat files in the exspected order
    """
    # Step 1: Remove non-numeric characters
    numeric_string = ''.join(filter(str.isdigit, os.path.basename(input_string)))

    # Step 2: Reverse the string
    reversed_string = numeric_string[::-1]

    # Step 3: Convert the reversed string to an integer
    result = int(reversed_string)

    # Print the result
    return result