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
            return True

        userinfo_logger.info('Creating custom authselect profile')
        
        try:
            # Use authselect create-profile to create the custom profile (without mkhomedir flag)
            subprocess.check_output(
                ['authselect', 'create-profile', 'ucs-join', '-b', 'sssd'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            # If create-profile fails, skip custom profile and use default with manual edits
            userinfo_logger.info('authselect create-profile failed, will use default profile with manual edits')
            return False
        
        # Add pam_group.so to system-auth
        system_auth_path = '/etc/authselect/custom/ucs-join/system-auth'
        if os.path.isfile(system_auth_path):
            with open(system_auth_path, 'r') as f:
                content = f.read()
            if 'pam_group.so' not in content:
                with open(system_auth_path, 'a') as f:
                    f.write('auth        required      pam_group.so use_first_pass\n')
                userinfo_logger.info('Added pam_group.so to custom profile system-auth')
        
        # Add pam_mkhomedir.so to password-auth and system-auth for home directory creation
        for auth_file in ['system-auth', 'password-auth']:
            auth_path = f'/etc/authselect/custom/ucs-join/{auth_file}'
            if os.path.isfile(auth_path):
                with open(auth_path, 'r') as f:
                    content = f.read()
                if 'pam_mkhomedir.so' not in content:
                    # Insert pam_mkhomedir.so in the session section
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if line.strip().startswith('session') and 'pam_mkhomedir.so' not in content:
                            # Add mkhomedir after the first session line
                            if 'pam_mkhomedir.so' not in '\n'.join(new_lines):
                                new_lines.append('session     required      pam_mkhomedir.so umask=0022 skel=/etc/skel')
                    with open(auth_path, 'w') as f:
                        f.write('\n'.join(new_lines))
                    userinfo_logger.info(f'Added pam_mkhomedir.so to {auth_file}')
        
        userinfo_logger.info('Custom authselect profile created')
        return True

    @execute_as_root
    def apply_custom_authselect_profile(self) -> None:
        userinfo_logger.info('Applying custom authselect profile')
        
        try:
            subprocess.check_output(
                ['authselect', 'select', 'custom/ucs-join', '--force'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            # Try with with-mkhomedir option
            userinfo_logger.info('Standard select failed, trying with with-mkhomedir')
            subprocess.check_output(
                ['authselect', 'select', 'custom/ucs-join', 'with-mkhomedir', '--force'],
                stderr=subprocess.STDOUT
            )
        
        userinfo_logger.info('Custom authselect profile applied')

    @execute_as_root
    def apply_default_profile_with_edits(self) -> None:
        userinfo_logger.info('Applying default sssd profile with manual edits')
        
        subprocess.check_output(
            ['authselect', 'select', 'sssd', 'with-mkhomedir', '--force'],
            stderr=subprocess.STDOUT
        )
        
        # Add pam_group.so to system-auth
        system_auth_path = '/etc/pam.d/system-auth'
        if os.path.isfile(system_auth_path):
            with open(system_auth_path, 'r') as f:
                content = f.read()
            if 'pam_group.so' not in content:
                with open(system_auth_path, 'a') as f:
                    f.write('auth        required      pam_group.so use_first_pass\n')
                userinfo_logger.info('Added pam_group.so to system-auth')
        
        userinfo_logger.info('Default profile with manual edits applied')

