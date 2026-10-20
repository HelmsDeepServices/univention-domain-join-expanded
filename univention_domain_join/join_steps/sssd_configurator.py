#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import os
import stat
import subprocess
from shutil import copyfile

from univention_domain_join.join_steps.root_certificate_provider import RootCertificateProvider
from univention_domain_join.utils.general import execute_as_root
from univention_domain_join.utils.ldap import get_machines_udm

userinfo_logger = logging.getLogger('userinfo')


class ConflictChecker(object):
    def sssd_conf_file_exists(self) -> bool:
        if os.path.isfile('/etc/sssd/sssd.conf'):
            userinfo_logger.warn('Warning: /etc/sssd/sssd.conf already exists.')
            return True
        return False


class SssdConfigurator(ConflictChecker):

    @execute_as_root
    def backup(self, backup_dir: str) -> None:
        if self.sssd_conf_file_exists():
            os.makedirs(os.path.join(backup_dir, 'etc/sssd'), exist_ok=True)
            copyfile(
                '/etc/sssd/sssd.conf',
                os.path.join(backup_dir, 'etc/sssd/sssd.conf')
            )

    @execute_as_root
    def backup_nsswitch(self, backup_dir: str) -> None:
        if os.path.isfile('/etc/nsswitch.conf'):
            os.makedirs(os.path.join(backup_dir, 'etc'), exist_ok=True)
            copyfile(
                '/etc/nsswitch.conf',
                os.path.join(backup_dir, 'etc/nsswitch.conf')
            )

    @execute_as_root
    def setup_sssd(self, dc_ip: str, ldap_master: str, ldap_server_name: str, admin_username: str, admin_pw: str, ldap_base: str, kerberos_realm: str, admin_dn: str, is_samba_dc: bool, config_sudo: bool, login_filter: str) -> None:
        self.ldap_password = open('/etc/machine.secret').read().strip()
        RootCertificateProvider().provide_ucs_root_certififcate(dc_ip)
        self.write_sssd_conf(dc_ip, ldap_master, ldap_server_name, admin_username, admin_pw, ldap_base, kerberos_realm, admin_dn, is_samba_dc, config_sudo, login_filter)
        self.configure_sssd()
        self.restart_sssd()

    @execute_as_root
    def write_sssd_conf(self, dc_ip: str, ldap_master: str, ldap_server_name: str, admin_username: str, admin_pw: str, ldap_base: str, kerberos_realm: str, admin_dn: str, is_samba_dc: bool, config_sudo: bool, login_filter: str) -> None:
        userinfo_logger.info('Writing /etc/sssd/sssd.conf ')
        if is_samba_dc:
            kpasswd_server = ldap_server_name
        else:
            kpasswd_server = ldap_master
        
        # Build sudo configuration if enabled
        sudo_config = ''
        if config_sudo:
            sudo_config = 'ldap_sudo_search_base = cn=sudo-ldap,cn=univention,%s\n' % (ldap_base,)
            sudo_config += 'ldap_sudo_full_refresh_interval = 180\n'
        
        # Build access filter configuration if provided
        access_config = ''
        if login_filter:
            access_config = 'access_provider = ldap\nldap_access_filter = %s\n' % (login_filter,)
        
        sssd_conf = \
            '[sssd]\n' \
            'config_file_version = 2\n' \
            'reconnection_retries = 3\n' \
            'sbus_timeout = 30\n' \
            'services = nss, pam, sudo\n' \
            'domains = %(kerberos_realm)s\n' \
            '\n' \
            '[nss]\n' \
            'reconnection_retries = 3\n' \
            '\n' \
            '[pam]\n' \
            'reconnection_retries = 3\n' \
            '\n' \
            '[sudo]\n' \
            '\n' \
            '[domain/%(kerberos_realm)s]\n' \
            'auth_provider = krb5\n' \
            'krb5_realm = %(kerberos_realm)s\n' \
            'krb5_server = %(ldap_server_name)s\n' \
            'krb5_kpasswd = %(kpasswd_server)s\n' \
            'id_provider = ldap\n' \
            'ldap_uri = ldap://%(ldap_server_name)s:7389\n' \
            'ldap_search_base = %(ldap_base)s\n' \
            'ldap_tls_reqcert = never\n' \
            'ldap_tls_cacert = /etc/univention/ssl/ucsCA/CAcert.pem\n' \
            'cache_credentials = true\n' \
            'enumerate = true\n' \
            'ldap_default_bind_dn = %(machines_ldap_dn)s\n' \
            'ldap_default_authtok_type = password\n' \
            'ldap_default_authtok = %(ldap_password)s\n' \
            '%(sudo_config)s%(access_config)s' \
            % {
                'kerberos_realm': kerberos_realm,
                'kpasswd_server': kpasswd_server,
                'ldap_base': ldap_base,
                'ldap_server_name': ldap_server_name,
                'ldap_password': self.ldap_password,
                'machines_ldap_dn': get_machines_udm(dc_ip, admin_username, admin_pw, admin_dn)[1],
                'sudo_config': sudo_config,
                'access_config': access_config,
            }
        with open('/etc/sssd/sssd.conf', 'w') as conf_file:
            conf_file.write(sssd_conf)
        os.chmod('/etc/sssd/sssd.conf', stat.S_IREAD | stat.S_IWRITE)

    @execute_as_root
    def configure_sssd(self) -> None:
        userinfo_logger.info('Configuring auth config profile for sssd')

        subprocess.check_output(
            ['pam-auth-update', '--enable', 'mkhomedir'],
            stderr=subprocess.STDOUT
        )

    @execute_as_root
    def restart_sssd(self) -> None:
        userinfo_logger.info('Restarting sssd')

        subprocess.check_output(
            ['service', 'sssd', 'restart'],
            stderr=subprocess.STDOUT
        )

    @execute_as_root
    def configure_nsswitch_for_sudo(self) -> None:
        userinfo_logger.info('Configuring nsswitch.conf for sudoers')

        nsswitch_path = '/etc/nsswitch.conf'

        try:
            with open(nsswitch_path, 'r') as f:
                lines = f.readlines()
        except IOError as e:
            userinfo_logger.error('Failed to read nsswitch.conf: %s' % e)
            raise

        # Check if sudoers line already contains sss
        sudoers_configured = False
        new_lines = []
        for line in lines:
            if line.strip().startswith('sudoers:'):
                if 'sss' in line:
                    userinfo_logger.info('sudoers already configured to use sss in nsswitch.conf')
                    sudoers_configured = True
                    new_lines.append(line)  # Keep the existing line
                else:
                    # Add sss to the line
                    new_line = line.rstrip() + ' sss\n'
                    new_lines.append(new_line)
                    sudoers_configured = True
            else:
                new_lines.append(line)

        if not sudoers_configured:
            # Add sudoers line at the end
            new_lines.append('sudoers: files sss\n')

        try:
            with open(nsswitch_path, 'w') as f:
                f.writelines(new_lines)
        except IOError as e:
            userinfo_logger.error('Failed to write nsswitch.conf: %s' % e)
            raise

        # Verify the change was written (only if we made changes)
        if not sudoers_configured:
            with open(nsswitch_path, 'r') as f:
                content = f.read()
                if 'sudoers:' not in content:
                    userinfo_logger.error('Failed to verify sudoers line in nsswitch.conf after write')
                    raise IOError('sudoers line not found in nsswitch.conf after write')

        if sudoers_configured:
            userinfo_logger.info('nsswitch.conf already has sudoers configured with sss')
        else:
            userinfo_logger.info('Configured nsswitch.conf for sudoers')
