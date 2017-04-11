#!/bin/bash
ufw logging on

ufw disable

# Set default rules

ufw default deny incoming
ufw default allow outgoing

# Now make specific exceptions

ufw allow 2200
ufw allow ntp
ufw allow www

ufw --force enable

# ufw status