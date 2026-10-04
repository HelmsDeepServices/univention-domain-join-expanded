#!/bin/bash

cleanup=false

while getopts "c" opt; do
    case "$opt" in
        c) cleanup=true ;;
    esac
done

if $cleanup; then
    echo "Cleaning Up Dependencies for *Rocky 9*"
    echo "Will remove packages below that are not dependencies of other installed packages:"
    echo "- python3"
    echo "- python3-dns"
    echo "- python3-ipython"
    echo "- python3-ldap"
    echo "- python3-netifaces"
    echo "- python3-setuptools"
    echo "- python3-pip"
    echo "- python3-wheel"
    echo "- python3-devel"
    echo "- git"
    echo "Will remove packages below outright, then run autoremove:"
    echo "- repo: crb"
    echo "- group: Development Tools"
    echo "WARNING: you may not want to run this on a machine you use for Python or C development. Verify each operation as script executes"
    read -r -p "Press [Enter] to continue..."
    rpm -e python3 python3-dns python3-ipython python3-ldap python3-netifaces python3-pip git python3-setuptools python3-wheel python3-devel
    dnf group remove "Development Tools"
    dnf config-manager --set-disabled crb
    dnf autoremove -y
else
    echo "Updating Repository Information, Upgrading all packages, and Installing Dependencies for *Rocky 9*"
    read -r -p "Press [Enter] to continue..."
    dnf update -y
    dnf install epel-release
    dnf config-manager --set-enabled crb
    dnf clean all
    dnf update -y
    dnf groupinstall "Development Tools"
    dnf install python3 sshpass krb5-workstation krb5-libs sssd-common sssd-client sssd sssd-client sssd-tools sssd-ldap sssd-krb5 python3-dns python3-ipython python3-ldap python3-netifaces python3-pip git openldap-devel cyrus-sasl-devel openldap openldap-clients python3-setuptools python3-wheel python3-devel wget oddjob-mkhomedir
    dnf install ntpsec
fi

