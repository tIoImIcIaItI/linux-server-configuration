#!/bin/bash

apache2ctl stop

# Prepare the catalog app postgresql database
echo "Configuring the database"
sudo -u postgres psql -f setupdb.sql


# Install the catalog app
echo "Copying the application"

if [ ! -d /webapps ]
then
    mkdir /webapps
else
	if [ -d /webapps/catalog ]
	then
		rm -rf /webapps/catalog
	fi
fi

cp -a -r ../catalog/. /webapps/catalog/


# Configure Appache to host the catalog app
echo "Configuring the web server"
cp www_conf.txt /etc/apache2/sites-enabled/000-default.conf
apache2ctl restart
