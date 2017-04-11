#!/bin/bash
# USAGE: ./create_user.sh username
username=$1

egrep "^$username" /etc/passwd >/dev/null
if [ $? != 0 ]; then
    homedir="/home/$username"
    # Create the user account and home directory, allowing only key-based logins
    echo "Creating useraccount $username"
    adduser --quiet --disabled-password --gecos "" $username
    
    # Copy the user's public key to the server
    echo "Establishing secure login"
    mkdir $homedir/.ssh
    cp $username".pub" $homedir/.ssh/authorized_keys
    chmod go-w $homedir
    chmod 700 $homedir/.ssh
    chmod 600 $homedir/.ssh/authorized_keys
    chown -hR $username:$username $homedir/.ssh/
    
    # Give the user sudo access
    echo "Granting sudo access"
    echo "$username ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$username
fi
