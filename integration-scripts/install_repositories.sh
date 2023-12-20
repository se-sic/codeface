#!/bin/sh

sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get -qqy install software-properties-common python-software-properties

echo "Adding R cran repositories"
version=`lsb_release -r | awk '{ print $2;}'`

deb https://cloud.r-project.org/bin/linux/ubuntu jammy-cran40/
wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | sudo tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc

gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9
gpg -a --export E084DAB9 | sudo apt-key add -

#echo "Adding node.js repository"
#sudo add-apt-repository -y ppa:chris-lea/node.js

sudo apt-get update -qq

