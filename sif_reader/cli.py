import os
import argparse
from glob import glob
import logging

import numpy as np
import pandas as pd

from . import parser as sif


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level = logging.INFO,
            format = '%(message)s'
        )

    files = []
    for p in args.pattern:
        files += glob(p)

    logging.info(f'Matched {files}')

    jdf = []
    for file in files:
        logging.info(f'Converting {file}')
        data, info = sif.parse(file)

        fn, _ = os.path.splitext(os.path.basename(file))

        df = pd.Series(
            data[:, 1],
            index = data[:, 0],
            dtype = int,
            name = 'counts'
        )
        df.index = df.index.rename('wavelength')

        if args.join:
            df = df.reset_index()
            df.columns = pd.MultiIndex.from_tuples([
                (fn, head) for head in df.columns
            ], names=('sample', 'index'))
            jdf.append(df)

        else:
            df.to_csv(f'{fn}.csv')

    if args.join:
        logging.info('Joining data')
        df = pd.concat(jdf, axis=1).sort_index(
            axis=1, level='sample', sort_remaining=False
        )

        fn = get_new_join_fn()
        df.to_csv(fn, index=False)


def get_parser():
    parser = argparse.ArgumentParser(description = 'Convert .sif file to .csv.')
    parser.add_argument(
        'pattern',
        nargs = '*',
        default = ['*.sif'],
        help = 'Glob pattern(s) to match files for conversion.'
    )

    parser.add_argument(
        '--join',
        action = 'store_true',
        help = 'Combine all data into a single file.'
    )

    parser.add_argument(
        '--verbose',
        action = 'store_true',
        help = 'Log actions.'
    )

    return parser


def get_new_join_fn() -> str:
    """
    :returns: A new file name used for saving joined data.
    """
    def _new_fn(i: int) -> str:
        basename = 'sif_joined_data'
        if i == 0:
            return f'{basename}.csv'

        return f'{basename}-{i}.csv'

    i = 0
    fn = _new_fn(i)
    while os.path.exists(fn):
        i += 1
        fn = _new_fn(i)

    return fn
        
