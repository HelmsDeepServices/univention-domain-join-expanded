<!--
SPDX-FileCopyrightText: 2017-2025 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
# Univention Domain Join Expanded

This is an assistant for joining Ubuntu, Debian, and other computers into Univention Corporate
Server (UCS) domains. It is based off the official Univention Domain Join package for Ubuntu 24.04 LTS. 
It will perform the following steps for you:

- Create an LDAP object for your Ubuntu computer on UCS
- Configure DNS
- Configure Kerberos
- Configure the login manager, if necessary
- Configure PAM
- Configure SSSD

Univention Domain Join supports the following Linux distributions:

- `ubuntu2404`
  - Ubuntu 24.04 LTS ("Noble Numbat")
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

The actual source code for the different releases can be found in
the corresponding git branches.

Univention Domain Join supports the Gnome and Unity desktop environments. The
configuration of the login manager of other desktop environments may not work,
but can be skipped using the `--skip-login-manager` parameter of the
`univention-domain-join-cli` tool.

# Limitations:

- Not tested with a desktop environment, only tested with `univention-domain-join-cli` and the `--skip-login-manager` flag.
- Configuration of the NTP server has been disabled. This is only necessary for Debian in containers (Such as LXC/Proxmox) and can be reenabled by uncommenting lines 73-76 of univention_domain_join/join_steps/kerberos_configurator.py. However, this feature has not been tested yet. In the future this should be added as a flag for the cli. 
- Operating system identification is handled using modified functions in univention_domain_join/utils/distributions.py which check for a Debian release. If Debian is identified, these functions will then return Ubuntu 24.04 to any of the other existing unmodified scripts that use them. While this appears harmless, all existing scripts need to be reviewed and adapted to Debian in the future. 

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
python -m pip install 
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
