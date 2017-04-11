#!/bin/bash
apt-get -qqy install apache2
apt-get -qqy install libapache2-mod-wsgi
apt-get -qqy install postgresql python-psycopg2
apt-get -qqy install python-flask python-sqlalchemy
apt-get -qqy install python-pip

pip install -U pip
pip install -U packaging
pip install -U setuptools
pip install -U six
pip install appdirs
pip install bleach
pip install requests
pip install -U httplib2
pip install -U oauth2client
