import os
import sys
import argparse
from glob import glob
import logging
from typing import Iterable

import pandas as pd

from . import utils


def main():
    """
    Main function for the CLI.
    Accepts glob patterns of file paths to parse as .sif files.
    Converts the matched files to .csv, either individually,
    or joined into a single file if using the `--join` flag.
    """
    parser = get_parser()
    args = parser.parse_args()

    paths = []
    for p in args.pattern:
        paths += glob(p)

    if len(paths) == 0:
        print('No files matched, aborting.')
        sys.exit(1)

    convert_files(
        paths,
        output_dir=args.output_dir,
        join=args.join,
        verbose=args.verbose
    )


def convert_files(
    paths: Iterable[str],
    output_dir = None,
    join: bool = False,
    verbose: bool = False
):
    """
    Converts sif files to csv.

    :param paths: Iterable of file paths to convert.
    :param output_dir: Path of directory ot output converted files to.
    :param join: Whether to join the output into a single file
        or place the output of each conversion in it own file.
        [Default: False]
    :param verbose: Whether to log info.
    """
    if len(paths) == 0:
        return

    if output_dir is None:
        output_dir = os.getcwd()
    
    else:
        output_dir = os.path.abspath(output_dir)

    if not os.path.exists(output_dir):
        raise FileNotFoundError(f'Output directory {output_dir} does not exist.')

    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )

    logging.info('Matched %s', paths)

    jdf = []
    for path in paths:
        logging.info('Converting %s', path)
        data, _ = utils.parse(path)

        fn, _ = os.path.splitext(os.path.basename(path))

        df = pd.Series(
            data[:, 1],
            index=data[:, 0],
            dtype=int,
            name='counts'
        )
        df.index = df.index.rename('wavelength')

        if join:
            df = df.reset_index()
            df.columns = pd.MultiIndex.from_tuples([
                (fn, head) for head in df.columns
            ], names=('sample', 'index'))
            jdf.append(df)

        else:
            df.to_csv(os.path.join(output_dir, f'{fn}.csv'))

    if join:
        logging.info('Joining data')
        df = pd.concat(jdf, axis=1).sort_index(
            axis=1, level='sample', sort_remaining=False
        )

        fn = get_new_join_fn(output_dir)
        df.to_csv(os.path.join(output_dir, fn), index=False)


def get_parser() -> argparse.ArgumentParser:
    """
    Creates the argument parser for the CLI.

    :returns ArgumentParser: Argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(description='Convert .sif file to .csv.')
    parser.add_argument(
        'pattern',
        nargs='*',
        default=['*.sif'],
        help='Glob pattern(s) to match files for conversion.'
    )

    parser.add_argument(
        '--output',
        dest='output_dir',
        help='Ouput directory to output converted files to.'
    )

    parser.add_argument(
        '--join',
        action='store_true',
        help='Combine all data into a single file.'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Log actions.'
    )

    return parser


def get_new_join_fn(directory: str) -> str:
    """
    :param directory: Directory to check.
    :returns: A new file name used for saving joined data.
    """
    def _new_fn(i: int) -> str:
        basename = 'sif_joined_data'
        if i == 0:
            return f'{basename}.csv'

        return f'{basename}-{i}.csv'

    i = 0
    fn = _new_fn(i)
    while os.path.exists(os.path.join(directory, fn)):
        i += 1
        fn = _new_fn(i)

    return fn
