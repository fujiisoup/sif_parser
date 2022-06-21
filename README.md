sif_reader
============

[![Build Status](https://travis-ci.com/fujiisoup/sif_reader.svg?branch=master)](https://travis-ci.com/fujiisoup/sif_reader)

## Basic usage

A small package to read Andor Technology Multi-Channel files.

It provides the following methods,

### `sif_reader.np_open`

Read '.sif' file and return as a `np.ndarray` for image and an `OrderedDict` for metadata.

```python
>>> import sif_reader
>>> data, info = sif_reader.np_open('/path/to/file.sif')
>>> data
array([[[887.  , 881.25, 875.65, ..., 866.05, 870.  ],
        [905.6 , 872.7 , 900.7 , ..., 871.4 , 866.45],
        ...,
        [885.6 , 879.4 , 873.5 , ..., 883.6 , 877.  ],
        [879.4 , 873.  , 880.5 , ..., 881.  , 867.  ]]],
      dtype=float32)
>>> info
OrderedDict([('SifVersion', 65559),
             ('ExperimentTime', 1254330082),
             ('DetectorTemperature', -100.0),
             ...
            ])
```

If your calibration data is included in the file, this will be included as
`info['Calibration_data']` or `info['Calibration_data_for_frame_1']`.

### `sif_reader.xr_open('/path/to/file.sif')`:

Read 'sif' file and return as a `xr.DataArray`.
The metadata is stored in `xr.DataArray.attrs`.
The calibration data and timestamps are stored as coordinates.

`xarray` is a very useful package to handle multi-dimensional arrays with metadata.
See [xarray project](http://xarray.pydata.org) for the details.

```python
>>> sif_reader.xr_open('testings/examples/image.sif')
<xarray.DataArray (Time: 1, height: 512, width: 512)>
array([[[887.  , 881.25, 875.65, ..., 866.05, 870.  ],
        [905.6 , 872.7 , 900.7 , ..., 871.4 , 866.45],
        [922.6 , 883.95, 899.  , ..., 864.6 , 864.8 ],
        ...,
        [880.65, 857.95, 883.55, ..., 866.  , 875.55],
        [885.6 , 879.4 , 873.5 , ..., 883.6 , 877.  ],
        [879.4 , 873.  , 880.5 , ..., 881.  , 867.  ]]],
      dtype=float32)
Coordinates:
  * Time     (Time) float64 0.0
Dimensions without coordinates: height, width
Attributes:
    SifVersion:            65559
    ExperimentTime:        1254330082
    DetectorTemperature:   -100.0
    ...
```

### `sif_reader.utils.extract_calibration`
The `Calibration_data` entry of `info` contains coefficients of a cubic
polynomial used to calculate the wavelengths of an image.
To facilitate this `sif_reader.utils` contains the `extract_calibration`
function, which returns the wavelength of each pixel.

```python
data, info = sif_reader.np_open('path/to/file.sif')
wavelengths = sif_reader.utils.extract_calibration(info)
```

### Use as a plugin for PIL

**NOTE!!  The current version does not work as a plugin, maybe due to updates in PIL. Contributions are very welcome.**
See the issue [#7](https://github.com/fujiisoup/sif_reader/issues/7)

We also provide a plugin for PIL,

```python
from PIL import image
import sif_reader.plugin

I = Image.open('/path/to/file.sif')
```

Note that, however, it does not work for multiple-image files.
Contribution is very welcome!
The image mode is `'F'`, 32-bit floating-point greyscale.


## History

This plugin is originally developed by [soemraws](https://github.com/soemraws)
based on Marcel Leutenegger's MATLAB script.


## Current status

Andor has changed `sif` format for many times.
Although I have tested this package with as many kinds of `sif` files as I have
(the test suit is always checking the compatibility, as the badge above shows),
it might be still incompatible with your particular `sif` file.

If your file cannot be read by this script,
please raise an issue in github.
If you send me your file, I can add your file into the test suit
(I have a private repo in order to keep your sif file private).

Contribution is also very welcome.


## License of original MATLAB script

Copyright (c) 2006, Marcel Leutenegger
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution
* Neither the name of the Ecole Polytechnique Fédérale de Lausanne, Laboratoire d'Optique Biomédicale nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
