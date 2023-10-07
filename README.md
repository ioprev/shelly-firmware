# shelly-firmware.py

This script attempts to make a fully functional binary image of the official Shelly firmware, based on the firmware update zip package found on http://api.shelly.cloud

The produced image can be used to revert a Shelly device to the official firmware, after being flashed with a third-party firmware like Tasmota, or totally bricked during flashing.

## Getting Started

To obtain the script, please make sure that you have `git` installed on your system, then download this git repository by running:
```bash
git clone https://github.com/ioprev/shelly-firmware.git
```

### Prerequisites

Python 3.7+ is suggested for running the script. The Python dependencies for this script can be installed on your system by following either of these methods:

Install via [poetry](https://python-poetry.org/docs/#installation): 

```
cd shelly-firmware
poetry install
```
 
### Installing SPIFFS tools

In addition to any Python dependencies, tools for editing the SPIFFS filesystem are required to be under the `tools` directory.
A script named `build_tools.sh` will fetch and build the tools from the [Mongoose OS vfs-fs-spiffs](https://github.com/mongoose-os-libs/vfs-fs-spiffs) repository.

For the build to be successful `make` tool and a working C compiler are required to be installed on the system. 

```
$ ./build_tools.sh
Cloning into 'fs-tools'...
Cloning into 'frozen'...
...
patching file tools/Makefile
...
GCC mkspiffs
GCC mkspiffs8
GCC unspiffs
GCC unspiffs8
```

The following binaries should now exist under `tools` directory:

```
mkspiffs8
unspiffs8
```

## Running

For running the script, please consult the output of `./shelly_firmware.py -h` command

```
$ ./shelly_firmware.py
INFO:	Shelly firmware binary download tool. Version 0.1
usage: shelly_firmware.py [-h] [-l] [-d MODEL] [-i INPUT_FILE] [-o OUTPUT]
                          [-v]

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            List available devices from shelly.cloud
  -d MODEL, --download MODEL
                        Download binary for specified device
  -i INPUT_FILE, --input INPUT_FILE
                        Use the provided .zip file as input, instead of
                        downloading.
  -o OUTPUT, --output OUTPUT
                        Output file name
  -v, --verbose         Enable debug output to console
```

This script is currently tested on `Shelly 1` and `Shelly 1PM` but should work with any device having 2MB of flash memory. Pull requests are welcome for any improvements. :)

## License

License: MIT
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Copyright (c) `2019` `Ioannis Prevezanos`

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
