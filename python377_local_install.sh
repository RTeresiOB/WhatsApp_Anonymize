#!/bin/bash

#########################################
# Installing python 3.7.7 locally.
# This script will install python
# into the ~/local/bin directory.
#########################################

FILE="~/local/bin/python3.7"

if [ -f "$FILE" ]; then
echo "$FILE exists.\n\n"
else
printf "$FILE does not exist \n Installing python3.7.7 into $FILE\n"
# installing python 3.7.7
mkdir -p ~/local
wget http://www.python.org/ftp/python/3.7.7/Python-3.7.7.tgz
tar xvzf Python-3.7.7.tgz
cd Python-3.7.7
./configure
make
make altinstall prefix=~/local  # specify local installation directory
ln -s ~/local/bin/python3.7 ~/local/bin/python
cd ..
fi
