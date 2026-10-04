#!/bin/bash

cleanup=false

while getopts "c" opt; do
    case "$opt" in
        v) verbose=true ;;
    esac
done

if $cleanup; then
    echo "Cleaning Up Dependencies for *Rocky 9*"
    echo "Will set the following packages to not manually installed, then run auto-remove:"
    echo "- python3"
    echo "- python3-dnspython"
    echo "- python3-ipy"
    echo "- python3-ldap"
    echo "- python3-netifaces"
    echo "- python3-venv"
    echo "- pip"
    echo "- git"
    read -r -p "Press [Enter] to continue..."
    apt-mark auto python3 python3-dnspython python3-ipy python3-ldap python3-netifaces pip git python3-venv
    apt autoremove -y --purge
else
    echo "Updating Repository Information, Upgrading all packages, and Installing Dependencies for *Rocky 9*"
    read -r -p "Press [Enter] to continue..."
    dnf update -y
    dnf install epel-release
    dnf config-manager --set-enabled crb
    dnf clean all
    dnf update -y
    dnf install python3 sshpass krb5-workstation krb5-libs sssd-common sssd-client sssd sssd-client sssd-tools sssd-ldap sssd-krb5 python3-dns python3-ipython python3-ldap python3-netifaces python3-pip git openldap-devel cyrus-sasl-devel openldap openldap-clients
    dnf install ntpsec
fi

