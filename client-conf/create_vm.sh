#!/bin/bash

# Delete the current VM instance, if any
vagrant destroy -f

# Delete the VM config, if any
if [ -f Vagrantfile ]
then
	rm Vagrantfile
fi

# Define a new VM
vagrant init ubuntu/trusty64

# sed -i '/# config.vm.network "forwarded_port", guest: 80, host: 8080/a config.vm.network :forwarded_port, guest: 22, host: 2222, id: "ssh"\' Vagrantfile
sed -i '/# config.vm.network "forwarded_port", guest: 80, host: 8080/a config.vm.network :forwarded_port, guest: 2200, host: 2200\' Vagrantfile
sed -i '/# config.vm.network "forwarded_port", guest: 80, host: 8080/a config.vm.network :forwarded_port, guest: 80, host: 8080\' Vagrantfile

# Instantiate and run the new VM
vagrant up
