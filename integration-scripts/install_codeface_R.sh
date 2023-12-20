#!/bin/sh
# Copyright Roger Meier <roger@bufferoverflow.ch>
# SPDX-License-Identifier:	Apache-2.0 BSD-2-Clause GPL-2.0+ MIT WTFPL

echo "Providing R libraries"

sudo apt install r-base-core=4.1.2-1ubuntu2
sudo apt install r-base-dev=4.1.2-1ubuntu2
sudo apt-mark hold r-base-core r-base-dev
sudo R CMD javareconf
sudo apt install r-cran-littler=0.3.15-1
sudo apt install r-cran-lattice=0.20-45-1
sudo apt install r-cran-zoo
sudo apt install r-cran-xts
sudo apt install r-cran-xtable
sudo apt install r-cran-reshape
sudo apt install r-cran-stringr
sudo apt install r-cran-scales
sudo apt install r-cran-rmysql
sudo apt install r-cran-rcurl
sudo apt install r-cran-nlme=3.1.155-1
sudo apt install r-cran-matrix=1.4-0-1
sudo apt install r-cran-mgcv=1.8-39-1
sudo apt install r-cran-rjson
sudo apt install r-cran-testthat
sudo apt install libx11-dev libssl-dev libssh2-1-dev libudunits2-dev

# install newer version of GDAL for compatibility with automatically selected packages
sudo add-apt-repository -y ppa:ubuntugis/ppa
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install libgdal-dev libgdal30

echo "Providing R libraries - packages.r"

sudo Rscript packages.r
