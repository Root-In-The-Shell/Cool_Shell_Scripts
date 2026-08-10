#!/bin/sh
#to move groups of files starting with same letters

SOURCE="/home/ishikawa/Documents/Test_1/"
DEST="/home/ishikawa/Documents/Test_2/"

echo "Copying files..."
cp "$SOURCE"R2* "$SOURCE"R0* "$DEST"/
echo "File copy complete!"
