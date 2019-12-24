#!/bin/bash

git clone https://github.com/mongoose-os-libs/vfs-fs-spiffs.git fs-tools
git clone https://github.com/cesanta/frozen.git frozen

(cd fs-tools && patch -p0) < esp8266.patch
(cd fs-tools/tools && make)

cp fs-tools/tools/mkspiffs8 .
cp fs-tools/tools/unspiffs8 .

rm -rf fs-tools
rm -rf frozen
