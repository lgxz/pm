#!/bin/bash

if [ $# == 0 ]
then
    SRC="~/Pictures/Photos Library.photoslibrary/originals"
    SRC="${SRC/#\~/$HOME}"
else
    SRC=$1
fi

echo "Import from: $SRC"
exiftool -csv -FileModifyDate -CreateDate -DateTimeOriginal -CreationDate -GPSDateTime -r "$SRC" | sed 1d >  exif.csv

