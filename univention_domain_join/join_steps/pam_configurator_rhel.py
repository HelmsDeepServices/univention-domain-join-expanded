#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import os
import subprocess
from shutil import copyfile

from univention_domain_join.utils.general import execute_as_root

userinfo_logger = logging.getLogger('userinfo')


class ConflictChecker(object):
    def group_conf_file_exists(self) -> bool:
        if os.path.isfile('/etc/security/group.conf'):
            userinfo_logger.warn('Warning: /etc/security/group.conf already exists.')
            return True
        return False

    def custom_authselect_profile_exists(self) -> bool:
        if os.path.isdir('/etc/authselect/custom/ucs-join'):
            userinfo_logger.warn('Warning: Custom authselect profile already exists.')
            return True
        return False


class PamConfigurator(ConflictChecker):

    @execute_as_root
    def backup(self, backup_dir: str) -> None:
        if self.group_conf_file_exists():
            os.makedirs(os.path.join(backup_dir, 'etc/security'), exist_ok=True)
            copyfile(
                '/etc/security/group.conf',
                os.path.join(backup_dir, 'etc/security/group.conf')
            )
        if self.custom_authselect_profile_exists():
            os.makedirs(os.path.join(backup_dir, 'etc/authselect/custom'), exist_ok=True)
            subprocess.check_output(
                ['cp', '-r', '/etc/authselect/custom/ucs-join', os.path.join(backup_dir, 'etc/authselect/custom/')],
                stderr=subprocess.STDOUT
            )

    def setup_pam(self) -> None:
        self.add_users_to_requiered_system_groups()
        self.create_custom_authselect_profile()
        self.apply_custom_authselect_profile()


    def add_users_to_requiered_system_groups(self) -> None:
        self.add_groups_to_group_conf()

    @execute_as_root
    def add_groups_to_group_conf(self) -> None:
        if self.group_conf_already_ok():
            return

        userinfo_logger.info('Adding  groups to /etc/security/group.conf ')

        # TODO: Would additional groups be appropriate here?
        with open('/etc/security/group.conf', 'a') as groups_file:
            groups_file.write(
                '*;*;*;Al0000-2400;audio,cdrom,dialout,floppy,plugdev,adm\n'
            )

    def group_conf_already_ok(self) -> bool:
        with open('/etc/security/group.conf', 'r') as groups_file:
            for line in groups_file:
                if '*;*;*;Al0000-2400;audio,cdrom,dialout,floppy,plugdev,adm\n' in line:
                    return True
        return False

    @execute_as_root
    def create_custom_authselect_profile(self) -> None:
        if self.custom_authselect_profile_exists():
            userinfo_logger.info('Custom authselect profile already exists, skipping creation')
            return

        userinfo_logger.info('Creating custom authselect profile')
        
        # Create custom profile directory
        os.makedirs('/etc/authselect/custom/ucs-join', exist_ok=True)
        
        # Copy base sssd profile files
        subprocess.check_output(
            ['cp', '-r', '/usr/share/authselect/default/sssd/*', '/etc/authselect/custom/ucs-join/'],
            stderr=subprocess.STDOUT
        )
        
        # Add pam_group.so to system-auth
        system_auth_path = '/etc/authselect/custom/ucs-join/system-auth'
        if os.path.isfile(system_auth_path):
            with open(system_auth_path, 'r') as f:
                content = f.read()
            if 'pam_group.so' not in content:
                with open(system_auth_path, 'a') as f:
                    f.write('auth        required      pam_group.so use_first_pass\n')
                userinfo_logger.info('Added pam_group.so to custom profile system-auth')
        
        # Create profile requirements file
        with open('/etc/authselect/custom/ucs-join/REQUIREMENTS', 'w') as f:
            f.write('sssd\n')
        
        userinfo_logger.info('Custom authselect profile created')

    @execute_as_root
    def apply_custom_authselect_profile(self) -> None:
        userinfo_logger.info('Applying custom authselect profile')
        
        subprocess.check_output(
            ['authselect', 'select', 'custom/ucs-join', '--force'],
            stderr=subprocess.STDOUT
        )
        
        userinfo_logger.info('Custom authselect profile applied')

