#!/bin/bash
# Initialize the VM
./create_vm.sh
# Create authentication keys for users
./create_keys.sh dking
./create_keys.sh grader
