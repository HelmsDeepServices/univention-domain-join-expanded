<!--
SPDX-FileCopyrightText: 2017-2025 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
# Univention Domain Join Expanded

This is an assistant for joining Ubuntu, Debian, Rocky Linux, and other computers into Univention Corporate
Server (UCS) domains. It is based off the official Univention Domain Join package for Ubuntu 24.04 LTS. 
It will perform the following steps for you:

- Create an LDAP object for your Ubuntu computer on UCS
- Configure DNS
- Configure Kerberos
- Configure the login manager, if necessary
- Configure PAM
- Configure SSSD

Univention Domain Join Extended supports the following Linux distributions:

- `ubuntu2604`
  - Ubuntu 26.04 LTS („Resolute Raccoon")
  - Ubuntu 26.04 LTS LXC (Proxmox)
- `ubuntu2404`
  - Ubuntu 24.04 LTS („Noble Numbat")
  - Ubuntu 24.04 LTS LXC (Proxmox)
- `ubuntu2204`
  - Ubuntu 22.04 LTS („Jammy Jellyfish“)
  - Ubuntu 22.04 LTS LXC (Proxmox)
  - Linux Mint 21 („Vanessa“)
- `debian13`
  - Debian 13 („Trixie“))
  - Debian 13 LXC (Proxmox)
- `debian12`
  - Debian 12 („Bookworm“))
  - Debian 12 LXC (Proxmox)
- `rocky10`
  - Rocky Linux 10.2 („Red Quartz“))
  - Rocky Linux 10.2 LXC (Proxmox)
- `rocky9`
  - Rocky Linux 9.8 („Blue Onyx“))
  - Rocky Linux 9.8 LXC (Proxmox)

The actual source code for the different releases can be found in
the corresponding git branches.

Univention Domain Join supports the Gnome and Unity desktop environments. The
configuration of the login manager of other desktop environments may not work,
but can be skipped using the `--skip-login-manager` parameter of the
`univention-domain-join-cli` tool.

# Limitations:

- Not tested with a desktop environment, only tested with `univention-domain-join-cli` and the `--skip-login-manager` flag.
- No apt or yum repository exists for these modifications (yet). Execution of these scripts is accomplished using a Python venv, please see below for instructions. 
- Updating NTP settings on Rocky Linux is not yet implemented properly. Need to switch to Chrony in the future, for now this can be done manually.
- Support for any Desktop Environments outside of the versions supported in the origonal/official Univention Domain Join application is not yet implemented. 

# Usage Reccomendations

```shell
usage: cli.py [-h] [--username USERNAME] [--password PASSWORD] [--password-file FILE] [--skip-login-manager] [--domain DOMAIN] [--dc-ip IP]
              [--force-ucs-dns] [--no-ntp-update] [--logfile FILE]

Tool for joining a client computer into an UCS domain.

options:
  -h, --help            show this help message and exit
  --username USERNAME   User name of a domain administrator
  --password PASSWORD   Password for the domain administrator
  --password-file FILE  Path to a file, containing the password for the domain administrator
  --skip-login-manager  Do not configure the login manager
  --domain DOMAIN       Domain name. Can be left out if the domain is configured for this system
  --dc-ip IP            IP address of the UCS domain controller to join to. Can be used if --domain does not work. If unsure, use the IP of the UCS Master
  --force-ucs-dns       Change the system's DNS settings and set the UCS DC as DNS nameserver (default is to use the standard network settings, but make
                        sure the your system can resolve the hostname of the UCS DC and the UCS master system)
  --no-ntp-update       Do not synchronize time with the DC via ntp
  --logfile, -L FILE    Path to log file /var/log/univention/domain-join-cli.log
```

- When using the CLI on a machine with no supported desktop environment installed, use `--skip-login-manager`
- When using the CLI inside a Proxmox LXC container, use `--no-ntp-update` since NTP is handled on the host OS. Ensure that your Proxmox host is configured to use the NTP server of your Univention Corperate Server instance. 

# Download and Installation

You can run these Python scripts on your Debian machine directly without installing the official Univention Domain Join package, which is only available as an Ubuntu PPA. 

## Clone the repository 

```shell
git clone https://github.com/HelmsDeepServices/univention-domain-join-expanded.git
```

## Install Dependencies:

Run the appropriate script from the dependencies/ directory for your OS as root.

```shell
sudo univention-domain-join-expanded/dependencies/debian12.sh
```

## Create a Virtual Environment, enter it, then install the source into the Virtual Environment.

```shell
cd univention-domain-join-expanded/
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

On Rocky Linux, run the following before `pip install .`...

```shell
pip install --upgrade pip setuptools wheel
```

## Attempt to run the `univention-domain-join-cli` tool and test root privileges.

```shell
sudo .venv/bin/python scripts/cli.py --help
```

## Execution and Cleanup

If you see the help text, the `univention-domain-join-cli` tool should now be functional. Simply replace `--help` in the command above with the flags you need. When finished, you can safely remove the git directory `univention-domain-join-expanded/` completely, as well as some dependencies by running the dependency script you ran origonally with the `-c` flag: 

```shell
sudo univention-domain-join-expanded/dependencies/debian12.sh -c
```

# Doc

Documentation on how to build and release this package to launchpad can be found [here](doc/dev.md)

# License

Univention Domain Join is built on top of many existing open source projects
which use their own licenses. The source code of all parts written by
Univention is licensed under the AGPLv3 . Please see the
[license file](./LICENSE) for more information.
