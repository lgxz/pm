#!/bin/bash

if [ $# == 0 ]
then
    echo "Usage: $0 dir"
    exit 0
fi

exiftool -csv -FileModifyDate -CreateDate -DateTimeOriginal -CreationDate -GPSDateTime -r "$1" | sed 1d >  exif.csv
find "$1" -type f -exec md5 -r {} \; | sed 's/ /,/' > md5.csv
join -t ',' -1 2 -2 1 md5.csv exif.csv > files.csv
rm -f md5.csv exif.csv

