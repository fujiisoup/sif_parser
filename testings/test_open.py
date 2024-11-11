import os
import sys
import glob
import codecs
import psutil


THIS_DIR = os.path.dirname(__file__)
sys.path.append(THIS_DIR + "/../sif_parser/")

# data directories that will be tested
DATA_DIR = THIS_DIR + "/sif_parser_testdata/"
PUBLIC_DATA_DIR = THIS_DIR + "/public_testdata/"
EXTRA_DATA_DIR = THIS_DIR + "/extra_data/"

import PIL.Image
import numpy as np
import os
import pytest
import unittest
import sif_parser
from sif_parser import utils
import _sif_open
import warnings


filenames = []
for d in [DATA_DIR, PUBLIC_DATA_DIR, EXTRA_DATA_DIR]:
    if os.path.exists(d):
        files = os.listdir(d)
        filenames += [d + f for f in files if f[-4:] in [".sif", ".SIF"]]


d = THIS_DIR + "/corrupt_data/"
files = os.listdir(d)
corrupt_filenames = [d + f for f in files if f[-4:] in [".sif", ".SIF"]]

d = THIS_DIR + "/spool_data/"
spool_file_dirs = []
for e in [d + "/data_corrupted/"]:
    if os.path.exists(e):
        spool_file_dirs += sorted(
            [e + dd for dd in os.listdir(e) if not dd.startswith(".DS")], key=str.lower
        )

spool_encoding_dirs = []
for e in [d + "/encodings/"]:
    if os.path.exists(e):
        spool_encoding_dirs += sorted(
            [e + dd for dd in os.listdir(e) if not dd.startswith(".DS")], key=str.lower
        )


def assert_file_not_in_use(filename):
    platform = sys.platform
    if platform == "linux":
        for proc in psutil.process_iter():
            try:
                for item in proc.open_files():
                    if filename == item.path:
                        raise Exception("File is in use.")
            except Exception:
                pass
        raise Exception("File is in use.")
    elif platform == "darwin":
        raise NotImplementedError('Testing in Mac is not supported.')
    elif platform == "win32":
        # for windows:
        os.rename(filename, filename)
    else:
        raise Exception("OS not supported")


def test_step_and_glue():
    filename = THIS_DIR + "/step_and_glue/step_and_glue.sif"
    with open(filename, "rb") as f:
        data, info = sif_parser.np_open(f)
    wl = sif_parser.utils.extract_calibration(info)

    expected_wl, expected_data = np.loadtxt(filename[:-3] + 'asc', skiprows=38).T
    assert np.allclose(wl, expected_wl)

    # xr_open
    data = sif_parser.xr_open(filename)
    assert np.allclose(data['calibration'], expected_wl)


@pytest.mark.parametrize(
    ("filename", "gate_width", "gate_delay", "gain"),
    [
        (THIS_DIR + "/issue37/shot25-Ar-delay 480us-width 2us-gain 3900.sif", 2000, 480000, 4095),
        (THIS_DIR + "/issue37/shot34-Ar-delay 470us-width 2us-gain 4095.sif", 2000, 470000, 4095),
    ],
)
def test_gatewidth(filename, gate_width, gate_delay, gain):
    # issue 33
    data, info = sif_parser.np_open(filename)
    assert "GateWidth" in info
    assert "GateDelay" in info
    assert "GateGain" in info
    assert np.allclose(info["GateWidth"], gate_width * 1e-9)
    assert np.allclose(info["GateDelay"], gate_delay * 1e-9)
    assert np.allclose(info["GateGain"], gain)
    assert np.allclose(info["GainDAC"], gain)

    
def test_issue27():
    filename = THIS_DIR + "/issue27/test.sif"
    with open(filename, "rb") as f:
        data, info = sif_parser.np_open(f)
    assert np.sum(np.isnan(data)) == 0


def test_issue33():
    filename = THIS_DIR + "/issue33/measurement.sif"

    with open(filename, "rb") as f:
        data, info = sif_parser.np_open(f)

    assert info["ExperimentTime"] == 1690545064
    assert info["DetectorTemperature"] == -25.0
    assert info["ExposureTime"] == 3.0
    assert info["CycleTime"] == 3.0221
    assert info["AccumulatedCycleTime"] == 3.0221
    assert info["AccumulatedCycles"] == 1
    assert info["StackCycleTime"] == 3.0221
    assert info["PixelReadoutTime"] == 1e-06
    assert info["GainDAC"] == 2500.0
    assert info["GateWidth"] == 1e-08
    assert info["GratingBlaze"] == 6.5e-06
    assert info["DetectorType"] == "DH334T-18F-63"
    assert info["GateWidth"] == 10e-9
    assert info["ShutterTime"] == (0.027, 0.0)
    assert info["spectrograph"] == '999'
    assert info["SifCalbVersion"] == 65540
    assert info["Calibration_data"] == [
        529.93812442523,
        0.061715845778342,
        -2.28349748230931e-07,
        -5.07163560661353e-11,
    ]
    assert info["FrameAxis"] == b"Wavelength"
    assert info["DataType"] == b"Counts"
    assert info["ImageAxis"] == b"Pixel number"
    assert info["NumberOfFrames"] == 20
    assert info["NumberOfSubImages"] == 1
    assert info["TotalLength"] == 20480
    assert info["ImageLength"] == 1024


@pytest.mark.parametrize("filename", filenames)
def test_open(filename):
    with open(filename, "rb") as f:
        data, info = sif_parser.np_open(f)
    assert np.sum(np.isnan(data)) == 0

    # open reference data if exists
    reffile = filename[:-4] + ".npz"
    if os.path.exists(reffile):
        ref = np.load(reffile)
        ref = ref[list(ref.keys())[0]]
        assert np.allclose(ref, data)


@pytest.mark.parametrize("filename", filenames)
def test_dask_open(filename):
    data, info = sif_parser.np_open(filename)
    data_lazy, info = sif_parser.np_open(filename, lazy="dask")
    assert np.allclose(data, data_lazy.compute())

    data_lazy, info = sif_parser.np_open(filename, lazy="dask")
    size = sys.getsizeof(data_lazy)
    size_compute = sys.getsizeof(data_lazy.compute())
    assert size < size_compute


@pytest.mark.parametrize("filename", filenames)
def test_xr_dask_open(filename):
    data = sif_parser.xr_open(filename)
    data_lazy = sif_parser.xr_open(filename, lazy="dask")
    assert np.allclose(data, data_lazy.compute())


@pytest.mark.parametrize("filename", filenames)
def test_memmap_open(filename):
    data, info = sif_parser.np_open(filename)
    data_lazy, info = sif_parser.np_open(filename, lazy="memmap")
    assert hasattr(data_lazy, "filename")
    assert not hasattr(data, "filename")
    assert np.allclose(data, data_lazy)


@pytest.mark.parametrize("filename", filenames)
def test_xr_memmap_open(filename):
    data = sif_parser.xr_open(filename)
    data_lazy = sif_parser.xr_open(filename, lazy="memmap")
    assert hasattr(data_lazy.data, "filename")
    assert not hasattr(data.data, "filename")
    assert np.allclose(data, data_lazy)


def test_one_image():
    with open(PUBLIC_DATA_DIR + "image.sif", "rb") as f:
        tile, size, n_frames, info = _sif_open._open(f)

    assert len(tile) == 1
    assert tile[0][1] == (0, 0, 512, 512)
    assert n_frames == 1


@pytest.mark.parametrize("filename", corrupt_filenames)
def test_corrupt_file(filename):
    with pytest.raises(ValueError) as e_info:
        data, info = sif_parser.np_open(filename)

    # try open with a write mode to make sure the file is closed
    assert_file_not_in_use(filename)

    with pytest.warns(UserWarning, match="corrupt."):
        data, info = sif_parser.np_open(filename, ignore_corrupt=True)

    with pytest.raises(ValueError) as e_info:
        data = sif_parser.xr_open(filename)

    with pytest.warns(UserWarning, match="corrupt."):
        data = sif_parser.xr_open(filename, ignore_corrupt=True)


@pytest.mark.parametrize(
    ("filename", "raman_wavelength"),
    [
        (THIS_DIR + "/raman_data/DD58_785_1_Fe2O3_5x10s.sif", 785),
        (THIS_DIR + "/raman_data/rubpy3 in ethanolpulsed.sif", 354.67),
    ],
)
def test_raman(filename, raman_wavelength):
    data, info = sif_parser.np_open(filename)
    assert "RamanExWavelength" in info
    print(info["RamanExWavelength"])
    assert np.allclose(info["RamanExWavelength"], raman_wavelength)


class TestCalibration(unittest.TestCase):
    """
    Test to make sure the calibration data is certainly read.
    """

    def setUp(self):
        self.filenames = []
        self.answer_files = []
        DATA_DIR2 = THIS_DIR + "/examples_with_calibration/"
        filenames = os.listdir(DATA_DIR2)
        for filename in filenames:
            if filename[-4:] == ".sif" or filename[-4:] == ".SIF":
                self.filenames.append(DATA_DIR2 + filename)
                self.answer_files.append(DATA_DIR2 + filename[:-4] + ".asc")

    def test_np_open(self):
        def read_lines(f):
            lines = []
            x = []
            for i, line in enumerate(f):
                try:
                    stripped = line.split()
                    array = np.array([float(v) for v in stripped])
                    if i == 0 or array.shape == lines[-1].shape:
                        lines.append(array)
                        x.append(array[0])
                except Exception:
                    break
            return np.array(x), np.array(lines)[:, 1:]

        for filename, answer_file in zip(self.filenames, self.answer_files):
            with open(filename, "rb") as f:
                actual, info = sif_parser.np_open(f)
            with open(answer_file, "rb") as f:
                expected_x, expected = read_lines(f)
                expected = expected.reshape(
                    actual.shape[0], actual.shape[2], actual.shape[1]
                )
                expected = np.moveaxis(expected, 1, -1)
            self.assertTrue(np.allclose(actual, expected))

            actual_x = utils.extract_calibration(info)
            if actual_x.ndim == 1:
                self.assertTrue(np.allclose(actual_x, expected_x))

            # test with xarray
            try:
                import xarray as xr

                # make sure it can be opened
                actual_xr = sif_parser.xr_open(filename)

            except ImportError:
                pass


try:
    import xarray as xr

    class Test_xr_open(unittest.TestCase):
        def test_xr_open2(self):
            da = sif_parser.xr_open(PUBLIC_DATA_DIR + "image.sif")
            self.assertTrue(np.sum(np.isnan(da)) == 0)
            self.assertTrue("timestamp_of_0" not in da.attrs.keys())
            self.assertTrue("Time" in da.coords)
            self.assertTrue("width" in da.dims)
            self.assertTrue("height" in da.dims)

        def test_multiple_open(self):
            filenames = []
            for d in [DATA_DIR, PUBLIC_DATA_DIR]:
                if os.path.exists(d):
                    files = os.listdir(d)
                    filenames += [d + f for f in files if f[-4:] in [".sif", ".SIF"]]

            outputfile = "test.nc"
            for filename in filenames:
                print("reading " + filename)
                with open(filename, "rb") as f:
                    data = sif_parser.xr_open(f)

                data.to_netcdf(outputfile)
                os.remove(outputfile)

except ImportError:
    pass


@pytest.mark.parametrize("spool_dir", spool_file_dirs)
def test_np_spool_open(spool_dir):
    """
    This test that the method "sif_parser.np_spool_open" is functional with
    missing or incomplete data.

    """
    with pytest.raises(ValueError) as e_info:
        data, info = sif_parser.np_spool_open(spool_dir, ignore_missing=False)

    with pytest.raises(ValueError) as e_info:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data, info = sif_parser.np_spool_open(spool_dir, ignore_missing=True)
            if data.shape != info["DetectorDimensions"]:
                raise ValueError()


@pytest.mark.parametrize("spool_dir", spool_encoding_dirs)
def test_np_spool_encoding(spool_dir):
    """
    This test that the data returned using the method "sif_parser.np_spool_open"
    is equal to that of the original data generated from the Andor Solis Software
    for the different encodings accepted [Mono32, 'Mono16', 'Mono12Packed'].

    """
    # get bit info from ini file
    ini_file = glob.glob(spool_dir + "/*.ini")
    with open(ini_file[0], "r", encoding="utf-8") as f:
        lines = f.readlines()
    keys, vals = map(
        list,
        zip(
            *[
                line.strip().split("=", 1)
                for line in lines
                if len(line.strip().split("=", 1)) == 2
            ]
        ),
    )
    keys = [i.strip() for i in keys]  # need to strip again
    vals = [i.strip() for i in vals]  # need to strip again
    ini_info = dict(zip(keys, vals))

    # load data using the sif_parser
    sifparser_data, info = sif_parser.np_spool_open(spool_dir)
    sifparser_data = np.swapaxes(sifparser_data, 1, 2)

    # load text data generated from the Solis software (ground truth data)
    text_list_files = sorted(glob.glob(spool_dir + "**/*.asc"))
    y_, x_ = info["size"]
    t = len(text_list_files)

    if ini_info["PixelEncoding"] in ["Mono16", "Mono12Packed"]:
        datatype = np.uint16
    elif ini_info["PixelEncoding"] == "Mono32":
        datatype = np.uint32

    data = np.empty([t, y_, x_], datatype)

    for frame in range(t):
        with codecs.open(text_list_files[frame], encoding="utf-8") as f:
            text_AndorSolis_data = np.loadtxt(f, max_rows=y_).astype(datatype)

        data[frame, ...] = text_AndorSolis_data[
            :, 1:
        ]  # remove firs row since show index info no data

    assert np.allclose(sifparser_data, data)

    # should be no error
    sif_parser.xr_spool_open(spool_dir)


def test_xr_spool_open_long():
    spool_dir = THIS_DIR + "/spool_data/data_corrupted/spool_very_long/"
    data = sif_parser.xr_spool_open(spool_dir, ignore_missing=True)
    assert np.all(np.diff(data["Time"].values) > 0)


if __name__ == "__main__":
    unittest.main()
