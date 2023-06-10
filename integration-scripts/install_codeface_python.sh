#!/bin/sh
# Copyright Roger Meier <roger@bufferoverflow.ch>
# SPDX-License-Identifier:	Apache-2.0 BSD-2-Clause GPL-2.0+ MIT WTFPL

echo "Providing codeface python"

sudo pip2 install --upgrade setuptools
sudo pip2 install --upgrade mock
sudo pip2 install --upgrade subprocess32

# Only development mode works
# install fails due to R scripts accessing unbundled resources!
# TODO Fix the R scripts
sudo python2.7 setup.py develop
