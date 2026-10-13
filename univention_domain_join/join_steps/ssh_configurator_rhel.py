#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import os
import subprocess
from shutil import copyfile

import pkg_resources

from univention_domain_join.utils.general import execute_as_root

userinfo_logger = logging.getLogger('userinfo')


class ConflictChecker(object):
    def sshd_config_exists(self) -> bool:
        if os.path.isfile('/etc/ssh/sshd_config'):
            userinfo_logger.warn('Warning: /etc/ssh/sshd_config already exists.')
            return True
        return False

    def sshd_config_already_configured(self) -> bool:
        if os.path.isfile('/etc/ssh/sshd_config'):
            with open('/etc/ssh/sshd_config', 'r') as f:
                for line in f:
                    # Check if line starts with AuthorizedKeysCommand (ignoring leading whitespace)
                    # and is not commented out
                    stripped_line = line.strip()
                    if stripped_line.startswith('AuthorizedKeysCommand'):
                        return True
        return False


class SshConfigurator(ConflictChecker):

    @execute_as_root
    def backup(self, backup_dir: str) -> None:
        if self.sshd_config_exists():
            os.makedirs(os.path.join(backup_dir, 'etc/ssh'), exist_ok=True)
            copyfile(
                '/etc/ssh/sshd_config',
                os.path.join(backup_dir, 'etc/ssh/sshd_config')
            )

    @execute_as_root
    def setup_ssh(self) -> None:
        if self.sshd_config_already_configured():
            userinfo_logger.info('SSH configuration already has AuthorizedKeysCommand, skipping')
            return

        self.install_ldap_keys_script()
        self.configure_sshd()
        self.restart_sshd()

    @execute_as_root
    def install_ldap_keys_script(self) -> None:
        userinfo_logger.info('Installing ldap-keys.sh script')

        # Get the script from package data
        try:
            script_source = pkg_resources.resource_filename('univention_domain_join', 'utils/ldap-keys.sh')
        except Exception as e:
            userinfo_logger.error(f'Failed to locate ldap-keys.sh in package: {e}')
            raise

        if not os.path.exists(script_source):
            userinfo_logger.error(f'ldap-keys.sh not found at {script_source}')
            raise FileNotFoundError(f'ldap-keys.sh not found at {script_source}')

        script_dest = '/usr/local/bin/ldap-keys.sh'

        copyfile(script_source, script_dest)
        os.chmod(script_dest, 0o755)
        userinfo_logger.info('Installed ldap-keys.sh to /usr/local/bin')

    @execute_as_root
    def configure_sshd(self) -> None:
        userinfo_logger.info('Configuring SSH daemon to use LDAP for SSH keys')

        sshd_config_path = '/etc/ssh/sshd_config'

        with open(sshd_config_path, 'r') as f:
            lines = f.readlines()

        # Check if the configuration already exists (ignoring commented lines)
        config_exists = any(line.strip().startswith('AuthorizedKeysCommand') for line in lines)

        if config_exists:
            userinfo_logger.info('AuthorizedKeysCommand already configured in sshd_config')
            return

        # Add the configuration to the end of the file
        with open(sshd_config_path, 'a') as f:
            f.write('\n# LDAP SSH key authentication\n')
            f.write('AuthorizedKeysCommand /usr/local/bin/ldap-keys.sh\n')
            f.write('AuthorizedKeysCommandUser root\n')

        userinfo_logger.info('Added AuthorizedKeysCommand configuration to sshd_config')

    @execute_as_root
    def restart_sshd(self) -> None:
        userinfo_logger.info('Restarting SSH daemon')

        subprocess.check_output(
            ['systemctl', 'restart', 'sshd'],
            stderr=subprocess.STDOUT
        )

        userinfo_logger.info('SSH daemon restarted successfully')
