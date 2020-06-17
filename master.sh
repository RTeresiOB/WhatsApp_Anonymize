#!/bin/sh

#  master.sh
#  
#
#  Created by Robert Teresi on 6/17/20.
#  

#########################################
# Master file.
# Takes 1 argument:
# Whether to use previously installed python
# (accessed via python command)
# Takes commands:
# y (python already installed) or
# n (python installed by this program)
#
#
#########################################

{ # try

py2or3="$(python -c 'import sys; print(sys.version_info[0])')" &&
pyv="$(python -c 'import sys; print(sys.version_info[1])')"

if ["$py2or3" = "3" ]; then
echo "Valid python"
else
echo "Need To install Python 3"
fi

} || { # catch
# save log for exception
}

if ["$1" = "y"]; then
printf " Using previously-installed Python.\n"
elif ["$1" = "n"]; then
printf " Using Python Version as installed by WhatsApp_Anonymize Repository."
else
x=0
while [ x = 0 ]
do
printf " No valid option selected. \n Please type in y to use previously-installed Python, n to use Python as installed by "
fi
