# Linux Server Configuration Submission

## Project Description

Take a baseline installation of a Linux distribution on a virtual machine and prepare it to host web applications, to include installing updates, securing it from a number of attack vectors and installing/configuring web and database servers.

## Running the Web App

Browse to [`http://udacity.davidjking.net/`](http://udacity.davidjking.net/) in a modern web browser.  

You will need a [Google account](https://accounts.google.com/signup) in order to create, edit, and delete categories and items within the app.

## Deployment Methodology

A local Vagrant VM was used initially to develop and test a set of deployment and configuration shell scripts for both the local and server systems.
On the local system, authentication keys were created for each user.
Next, the scripts and supporting files were copied from local to server using `scp`, and then executed to fully prepare the server upon completion.
The local key generation script is not included in the repository, as a security consideration.

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

#### Web
- Apache w/WSGI (apache2, libapache2-mod-wsgi)

#### Database

- PostgreSQL (`postgresql`, `python-psycopg2`)
- SqlAlchemy (`python-sqlalchemy`)

#### Application
- Python 2.7
- Flask (`python-flask`)

### Notable Configuration Changes

- System software updated and upgraded
- Installed NTP, set system time-zone to UTC
- Configured and enabled UFW firewall
- SSH running on non-standard port
- Created and configured `grader` user account with key-based authentication
- Disabled password-based logins
- Installed and configured web server, database server
- Installed web app and dependencies
- Created and configured application database, user, and permissions

## Attributions
