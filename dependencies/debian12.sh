#!/bin/bash

cleanup=false

while getopts "c" opt; do
    case "$opt" in
        v) verbose=true ;;
    esac
done

if $cleanup; then
    echo "Cleaning Up Dependencies for *Debian 12*"
    echo "Will set the following packages to not manually installed, then run auto-remove:"
    echo "- python3"
    echo "- python3-dnspython"
    echo "- python3-ipy"
    echo "- python3-ldap"
    echo "- python3-netifaces"
    echo "- pip"
    echo "- git"
    read -r -p "Press [Enter] to continue..."
    apt-mark auto python3 python3-dnspython python3-ipy python3-ldap python3-netifaces pip git
    apt autoremove -y --purge
else
    echo "Installing Dependencies for *Debian 12*"
    apt update
    apt install python3 sshpass heimdal-clients libsss-sudo libpam-sss libnss-sss sssd python3-dnspython python3-ipy python3-ldap python3-netifaces pip git libldap2-dev libsasl2-dev libldap-common
fi

