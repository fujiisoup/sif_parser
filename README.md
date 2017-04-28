sif
====

A small library to read Andor Technology Multi-Channel files.

It provides the following methods,

+ `sif.np_open('/path/to/file.sif')`:
Read 'sif' file and return as a `np.ndarray` and a `OrderedDict`.

+ `sif.xr_open('/path/to/file.sif')`:
Read 'sif' file and return as a `xr.DataArray`. For `xr.DataArray`,
see [xarray project](http://xarray.pydata.org)

We also provides a plugin for PIL,

```python
from PIL import image
import sif.plugin

I = Image.open('/path/to/file.sif')
```

Note that, however, it seems unstable.


Image mode for PIL data
------------------------

The image mode is `'F'`, 32-bit floating-point greyscale.



Metadata
--------

Most of the known metadata is returned by `np_open` method,
or stored in `attrs` attribute of `xr.DataArray` for `xr_open` method.

In PIL-plugin mode, metadata is stored in the image's `info` dictionary.


History
-------

This plugin is originally developed by ***
based on Marcel Leutenegger's MATLAB script.


Version compatibility
-----------------------
Andor has changed `sif` format many times.
The current version can be incompatible with some `sif` file.
If your `sif` file cannot be read by this script,
please raise an issue in github, with attaching an example file.
Contribution is also very welcome.


License of original MATLAB script
---------------------------------

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
