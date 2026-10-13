#!/bin/sh

# bash script to be used in sshd AuthorizedKeysCommand

# Copyright (C) 2023-2025 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3. If not, see <https://www.gnu.org/licenses/>.

# This script retrieves SSH public keys from LDAP for a given username
# Usage: ldap-keys.sh <username>
# It reads LDAP connection parameters from /etc/sssd/sssd.conf

# Read LDAP configuration from sssd.conf
SSSD_CONF="/etc/sssd/sssd.conf"

if [ ! -f "$SSSD_CONF" ]; then
    echo "Error: $SSSD_CONF not found" >&2
    exit 1
fi

# Extract LDAP parameters from sssd.conf
LDAP_URI=$(grep -E '^ldap_uri ' "$SSSD_CONF" | sed 's/ldap_uri = //' | tr -d '[:space:]')
LDAP_BASE=$(grep -E '^ldap_search_base ' "$SSSD_CONF" | sed 's/ldap_search_base = //' | tr -d '[:space:]')
LDAP_BIND_DN=$(grep -E '^ldap_default_bind_dn ' "$SSSD_CONF" | sed 's/ldap_default_bind_dn = //' | tr -d '[:space:]')
LDAP_BIND_PW=$(grep -E '^ldap_default_authtok ' "$SSSD_CONF" | sed 's/ldap_default_authtok = //' | tr -d '[:space:]')
LDAP_TLS_CACERT=$(grep -E '^ldap_tls_cacert ' "$SSSD_CONF" | sed 's/ldap_tls_cacert = //' | tr -d '[:space:]')
LDAP_TLS_REQCERT=$(grep -E '^ldap_tls_reqcert ' "$SSSD_CONF" | sed 's/ldap_tls_reqcert = //' | tr -d '[:space:]')

if [ -z "$LDAP_URI" ] || [ -z "$LDAP_BASE" ]; then
    echo "Error: Could not read LDAP configuration from $SSSD_CONF" >&2
    exit 1
fi

# Username to search for
USERNAME="$1"

if [ -z "$USERNAME" ]; then
    echo "Error: Username not provided" >&2
    exit 1
fi

# Perform LDAP search for SSH public keys
if [ -n "$LDAP_BIND_DN" ] && [ -n "$LDAP_BIND_PW" ]; then
    # Use authenticated bind
    # Try without TLS first (for UCS port 7389 which may not require TLS for machine accounts)
    RESULT=$(ldapsearch -x -H "$LDAP_URI" -b "$LDAP_BASE" \
        -D "$LDAP_BIND_DN" -w "$LDAP_BIND_PW" \
        -LLL "(&(objectClass=posixAccount)(uid=$USERNAME))" sshPublicKey \
        2>/dev/null)

    # If that fails and we have TLS cert, try with TLS
    if [ -z "$RESULT" ] && [ -n "$LDAP_TLS_CACERT" ] && [ -f "$LDAP_TLS_CACERT" ]; then
        RESULT=$(ldapsearch -x -H "$LDAP_URI" -b "$LDAP_BASE" \
            -D "$LDAP_BIND_DN" -w "$LDAP_BIND_PW" \
            -ZZ -o nettimeout=5 \
            -LLL "(&(objectClass=posixAccount)(uid=$USERNAME))" sshPublicKey \
            2>/dev/null)
    fi

    # Extract SSH keys from the result - handle multiline keys properly
    # Use perl to handle potential line folding in LDAP output
    echo "$RESULT" | perl -00 -ne 'print "$1\n" while /sshPublicKey:\s*(.+?)(?=\n\S|\n\n|$)/gs'
else
    # Use anonymous bind (if allowed)
    RESULT=$(ldapsearch -x -H "$LDAP_URI" -b "$LDAP_BASE" \
        -LLL "(&(objectClass=posixAccount)(uid=$USERNAME))" sshPublicKey \
        2>/dev/null)
    echo "$RESULT" | perl -00 -ne 'print "$1\n" while /sshPublicKey:\s*(.+?)(?=\n\S|\n\n|$)/gs'
fi
