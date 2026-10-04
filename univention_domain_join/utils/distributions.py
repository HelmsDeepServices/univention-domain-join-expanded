#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess


#def get_distribution() -> str:
#    return subprocess.check_output(['lsb_release', '-is']).strip().decode()

def get_distribution() -> str:
    with open('/etc/os-release') as f:
        os_release = {}
        for line in f:
            line = line.strip()
            if not line or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os_release[key] = value.strip('"')

    distribution = os_release['ID']

    if distribution == 'debian':
        return 'Ubuntu'

    return distribution.capitalize()

#def get_release() -> str:
#    return subprocess.check_output(['lsb_release', '-rs']).strip().decode()

def get_release() -> str:
    with open('/etc/os-release') as f:
        os_release = {}
        for line in f:
            line = line.strip()
            if not line or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os_release[key] = value.strip('"')

    if os_release.get('ID') == 'debian':
        if os_release.get('VERSION_ID') == '13':
            return '26.04'
        return '24.04'

    if os_release.get('ID') == 'rocky':
        return os_release.get('VERSION_ID', '9')

    return subprocess.check_output(
        ['lsb_release', '-rs']
    ).strip().decode()
