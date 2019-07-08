#!/bin/bash

if [ $# == 0 ]
then
    SRC="~/Pictures/Photos Library.photoslibrary/originals"
    SRC="${SRC/#\~/$HOME}"
else
    SRC=$1
fi

echo "SRC is $SRC"

exiftool -csv -FileModifyDate -CreateDate -DateTimeOriginal -CreationDate -GPSDateTime -r "$SRC" | sed 1d >  exif.csv
find "$SRC" -type f -exec md5 -r {} \; | sed 's/ /,/' > md5.csv
join -t ',' -1 2 -2 1 md5.csv exif.csv > files.csv
rm -f md5.csv exif.csv

