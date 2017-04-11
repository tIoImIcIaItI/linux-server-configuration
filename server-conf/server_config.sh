#!/bin/bash

echo "Performing initial system update"

# Ensure basic system software is installed and updated
apt-get -qqy update
apt-get -qqy upgrade
apt-get -qqy install ntp
apt-get -qqy install ufw

# Set the server to UTC
timedatectl set-timezone UTC

# Lockdown the firewall
echo "Configuring firewall"
./config_ufw.sh

# Set SSH to listen on a non-default port
sed -i 's/Port 22/Port 2200/' /etc/ssh/sshd_config
service ssh restart
#grep 'Port' /etc/ssh/sshd_config
#netstat -lntp | grep "2200"


# Create user accounts
echo "Creating user accounts"
./create_user.sh dking
./create_user.sh grader

# Force secure authentication
echo "Enforcing secure logins"
./disable_pwd_auth.sh

# Update and install server and applicaiton software
echo "Installing software"
./install_prerequisites.sh
./install_apps.sh
