import os
import sys
from glob import glob
import shutil
import typing
import logging

import numpy as np
import pandas as pd

from sif_parser import cli


THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + '/../sif_parser/')

# data directories that will be tested
PUBLIC_DATA_DIR = THIS_DIR + '/public_testdata/'

CLI_DATA_DIR = os.path.join(PUBLIC_DATA_DIR, 'cli')
CLI_REF_DIR = os.path.join(CLI_DATA_DIR, 'reference')
CLI_OUT_DIR = os.path.join(CLI_DATA_DIR, 'output')


def clean_out_dir():
    """Delete output directory and recreate for fresh start."""
    try:
        shutil.rmtree(CLI_OUT_DIR)

    except FileNotFoundError:
        # output directory did not exist
        pass

    os.mkdir(CLI_OUT_DIR)


def get_reference_path(data_path: str) -> str:
    """
    :param data_path: Path to the converted (csv) data file.
    :returns: Path of the corresponding reference data.
    :raises FileNotFoundError: If corresponding reference path does not exist.
    """
    _, fn = os.path.split(data_path)
    ref_path = os.path.join(CLI_REF_DIR, fn)
    if not os.path.exists(ref_path):
        raise FileNotFoundError(
            f'Data file {data_path} does not have a corresponding reference file. {ref_path} does not exist.')

    return ref_path


def dfs_are_equal(
    df0,
    df1,
    index_precision: typing.Union[int, None] = None
) -> bool:
    """
    Compare if two dataframes are equal.
    Compares both the index and the values.

    :param df0: Pandas DataFrame.
    :param df1: Pandas DataFrame.
    :param index_precision: Number of decimals to round to for indicies.
        None to perform no rounding.
        [Default: None]
    :returns: Whether the two DataFrames are equal.
    """
    df0 = df0.copy()
    df1 = df1.copy()

    # round index to sig figs
    if index_precision is not None:
        df0.index = np.around(df0.index, index_precision)
        df1.index = np.around(df1.index, index_precision)

    try:
        cdf = (df0 == df1)

    except ValueError:
        # indices did not match
        return False

    return cdf.all().all()


def test_convert_files():
    """
    Validate CLI correctily parses file.
    """
    clean_out_dir()
    paths = glob(os.path.join(CLI_DATA_DIR, '*.sif'))
    cli.convert_files(paths, output_dir=CLI_OUT_DIR)

    converted = glob(os.path.join(CLI_OUT_DIR, '*.csv'))
    if len(converted) == 0:
        assert False

    for p in converted:
        ddf = pd.read_csv(p, index_col='wavelength')
        rdf = pd.read_csv(get_reference_path(p), index_col='wavelength')
        assert dfs_are_equal(ddf, rdf, index_precision=1)


def test_convert_files_join():
    """
    Validate CLI joins all data when using --join flag.
    """
    clean_out_dir()
    paths = glob(os.path.join(CLI_DATA_DIR, '*.sif'))
    cli.convert_files(paths, output_dir=CLI_OUT_DIR, join=True)

    converted = glob(os.path.join(CLI_OUT_DIR, '*.csv'))
    if len(converted) == 0:
        assert False

    for p in converted:
        ddf = pd.read_csv(p)
        rdf = pd.read_csv(get_reference_path(p))
        assert dfs_are_equal(ddf, rdf)


def test_convert_files_verbose(caplog):
    """
    Validate CLI prints matched files when using --verbose flag.
    """
    clean_out_dir()
    caplog.set_level(logging.INFO)
    paths = glob(os.path.join(CLI_DATA_DIR, '*.sif'))
    cli.convert_files(paths, output_dir=CLI_OUT_DIR, verbose=True)

    messages = caplog.messages

    # check first message displays all files
    # first message should be "Matched [<paths>]"
    for p in paths:
        p = p.replace('\\', '/')
        assert p in ''.join(messages[0]).replace('\\\\', '\\').replace('\\', '/')

    # check each path has a converted message
    conv_msgs = map(lambda p: f'Converting {p}', paths[1:])
    for m in conv_msgs:
        m = m.replace('\\', '/')
        assert m in ''.join(messages[1:]).replace('\\\\', '\\').replace('\\', '/')


def test_get_new_join_fn():
    """
    Validate get_new_join_fn returns a new file name.
    First join should be  saved at `sif_joined_data.csv`
    Subsequent should be saved at `sif_joined_data-<n>.csv`
    """
    clean_out_dir()
    paths = glob(os.path.join(CLI_DATA_DIR, '*.sif'))

    cli.convert_files(paths, output_dir=CLI_OUT_DIR, join=True)
    assert os.path.exists(os.path.join(CLI_OUT_DIR, 'sif_joined_data.csv'))

    cli.convert_files(paths, output_dir=CLI_OUT_DIR, join=True)
    assert os.path.exists(os.path.join(CLI_OUT_DIR, 'sif_joined_data-1.csv'))
