# shelly-firmware.py

This script attempts to make a fully functional binary image of the official Shelly firmware, based on the firmware update zip package found on http://api.shelly.cloud
The produced image can be used to revert a Shelly device to the official firmware, after being flashed with a third-party firmware like Tasmota, or totally bricked during flashing.

## Getting Started

To obtain the script, please make sure that you have `git` installed on your system, then download this git repository by running:
`git clone https://github.com/ioprev/shelly-firmware.git`

### Prerequisites

Python 3.7+ is suggested for running the script. The Python dependencies for this script can be installed on your system by following either of these methods:

a) Install system-wide by using pip

```
$ cd shelly-firmware
$ pip3 install -r requirements.txt
...
Installing collected packages: requests, sh
Successfully installed requests-2.22.0 sh-1.12.14
```

b) Create a Python virtualenv by using `pipenv`. `pipenv` can be installed by [following the instructions](https://github.com/pypa/pipenv#installation)

```
$ cd shelly-firmware
$ pipenv install
...
✔ Success!
Updated Pipfile.lock (417959)!
Installing dependencies from Pipfile.lock (417959)…
  🐍   ▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉ 6/6 — 00:00:02

$ pipenv shell
...
(shelly-firmware) bash-3.2$

```
 
### Installing SPIFFS tools

In addition to any Python dependencies, tools for editing the SPIFFS filesystem are required to be under the `tools` directory.
A script named `build_tools.sh` will fetch and build the tools fromthe [Mongoose OS vfs-fs-spiffs](https://github.com/mongoose-os-libs/vfs-fs-spiffs) repository

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
$ ls -1 unspiffs8 mkspiffs8
mkspiffs8
unspiffs8
```

## Running

For running the script, please consult the output of `./shelly_firmware.py -h` command

```
$ ./shelly_firmware.py -h
usage: shelly_firmware.py [-h] [-l] [-d MODEL] [-o OUTPUT] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            List available devices from shelly.cloud
  -d MODEL, --download MODEL
                        Download binary for specified device
  -o OUTPUT, --output OUTPUT
                        Output file name
  -v, --verbose         Enable debug output to console
```

## License

[![License: CC BY 4.0](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/)
