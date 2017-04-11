# Linux Server Configuration Project

## Project Description

Take a baseline installation of a Linux distribution on a virtual machine and prepare it to host web applications, to include installing updates, securing it from a number of attack vectors and installing/configuring web and database servers.

## Running the Web App

Browse to [`http://udacity.davidjking.net/`](http://udacity.davidjking.net/) in a modern web browser.  

You will need a [Google account](https://accounts.google.com/signup) in order to create, edit, and delete categories and items within the app.

## Deployment Methodology

A local Vagrant VM was used initially to develop and test a set of deployment and configuration shell scripts for both the local and server systems. Most of these scripts are included in the repository.

On the local system, scripts created authentication keys for each user.
Scripts and supporting files were then deployed to the server and executed, to fully prepare the server upon completion.

The local key generation script, generated keys, and other sensitive information is not included in the repository for obvious reasons.

## Server Information

Hosting Provider: [Amazon Lightsail](https://amazonlightsail.com/)

### Public IP
`34.203.53.142`

### SSH
Username: `grader`  
Host: `34.203.53.142`  
Port: `2200`  
Private Key: *supplied separately*  
Pass-phrase: *supplied separately*

Example: `ssh grader@34.203.53.142 -i ~/.ssh/grader -p 2200`

### Application Database
Database Name: `itemcatalog`  
User Name: `catalog`  
Permissions: SELECT, INSERT, UPDATE, DELETE on tables, sequences

### Web Application
Source: `/webapps/catalog/`  
Entry-point: `/webapps/catalog/catalog.wsgi`  

### Notable Software & Libraries Used

#### Web Server
- Apache w/WSGI (apache2, libapache2-mod-wsgi)

#### Database Server

- PostgreSQL (`postgresql`, `python-psycopg2`)
- SqlAlchemy (`python-sqlalchemy`)

#### Application Framework
- Python 2.7
- Flask (`python-flask`)

The web application itself is a derivative of my [item-catalog](https://github.com/tIoImIcIaItI/item-catalog) project, enhanced to be more configurable in a hosted environment.

### Notable Configuration Changes

- System software updated and upgraded
- Installed NTP, set system time-zone to UTC
- Configured and enabled UFW firewall
- SSH running on non-standard port
- Created and configured `grader` user account with key-based authentication
- Disabled password-based logins
- Installed, configured and secured web server, database server
- Installed web app and dependencies
- Created and configured application database, user, and permissions

The web server is not configured to serve any static files. In combination with the web app serving only generated content and files from safe locations, this limits public access appropriately.

The application database login is limited to CRUD operations on the app database only.

## Attributions
See my [item-catalog](https://github.com/tIoImIcIaItI/item-catalog) project for sources used to create the web application itself.

The setup scripts are entirely a product of hundreds of Google searches for all the bits and pieces needed to automate the process from the Bash shell. Primary sources include the following.
- `man` and help pages for all commands used
- [Ask Ubuntu](https://askubuntu.com/)
- [Stack Overflow](http://stackoverflow.com/)
- [Apache](https://httpd.apache.org/docs/)
- [Udacity](https://www.udacity.com/)

## Known Issues
Currently the application database connection info is set manually after deployment. The code should instead be getting this information from an external source (configuration file, environment variable, or similar).
