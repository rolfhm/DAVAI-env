#!/usr/bin/env python3
# -*- coding:Utf-8 -*-
"""
Davai environment around experiments and shelves.
"""
from __future__ import print_function, absolute_import, unicode_literals, division

import os
import re
import configparser
import socket
import io
import subprocess

_package_rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__path__[0])))  # realpath to resolve symlinks
__version__ = io.open(os.path.join(_package_rootdir, 'VERSION'), 'r').read().strip()
__this_repo__ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# fixed parameters
DAVAI_RC_DIR = os.path.join(os.environ['HOME'], '.davairc')
DAVAI_PROFILE = os.path.join(DAVAI_RC_DIR, 'profile')
DAVAI_XP_COUNTER = os.path.join(DAVAI_RC_DIR, '.last_xp')
DAVAI_XPID_SYNTAX = 'dv-{xpid_num:04}-{host}@{user}'
DAVAI_XPID_RE = re.compile('^' + DAVAI_XPID_SYNTAX.replace('{xpid_num:04}', '\d+').
                                                   replace('-{host}', '(-\w+)?').
                                                   replace('{user}', '\w+') + '$')
CONFIG_BASE_FILE = os.path.join(__this_repo__, 'conf', 'base.ini')
CONFIG_USER_FILE = os.path.join(DAVAI_RC_DIR, 'user_config.ini')
CONFIG_TEMPLATE_USER_FILE = os.path.join(__this_repo__, 'templates', 'user_config.ini')


def guess_host():
    """
    Guess host from (by order of resolution):
      - presence as 'host' in section [hosts] of base and user config
      - resolution from socket.gethostname() through RE patterns of base and user config
    """
    host = config.get('hosts', 'host', fallback=None)
    if not host:
        socket_hostname = socket.gethostname()
        for h, pattern in config['hosts'].items():
            if re.match(pattern, socket_hostname):
                host = h[:-len('_re_pattern')]  # h is '{host}_re_pattern'
                break
    if not host:
        raise ValueError(("Couldn't find 'host' in [hosts] section of config files ('{}', '{}'), " +
                          "nor guess from hostname ({}) and keys '*host*_re_pattern' " +
                          "in section 'hosts' of same config files.").format(
            CONFIG_USER_FILE, CONFIG_BASE_FILE, socket_hostname))
    return host


# CONFIG
config = configparser.ConfigParser()
config.read(CONFIG_BASE_FILE)
# read user config a first time to help guessing host
if os.path.exists(CONFIG_USER_FILE):
    config.read(CONFIG_USER_FILE)
# then complete config with host config file
CONFIG_HOST_FILE = os.path.join(__this_repo__, 'conf', '{}.ini'.format(guess_host()))
if os.path.exists(CONFIG_HOST_FILE):
    config.read(CONFIG_HOST_FILE)
# and read again user config so that it overwrites host config
if os.path.exists(CONFIG_USER_FILE):
    config.read(CONFIG_USER_FILE)

# Initialization and update functions -----------------------------------------

def init(token=None):
    """
    Initialize Davai env for user.
    """
    from .util import expandpath, export_token_in_profile  # import inside function because of circular dependency
    from .util import preset_user_config_file
    # Setup directories
    print("Setup DAVAI home directory ({}) ...".format(config.get('paths', 'davai_home')))
    for d in ('davai_home', 'experiments', 'logs', 'default_mtooldir'):
        p = expandpath(config.get('paths', d))
        if os.path.exists(p):
            if not os.path.isdir(p):
                raise ValueError("config[paths][{}] is not a directory : '{}'".format(d, p))
        else:
            if '$' in p:
                raise ValueError("config[paths][{}] is not expandable : '{}'".format(d, p))
            os.makedirs(p)
    # Set rc
    print("Setup {} ...".format(DAVAI_RC_DIR))
    if not os.path.exists(DAVAI_RC_DIR):
        os.makedirs(DAVAI_RC_DIR)
    # Link bin (to have command line tools in PATH)
    link = os.path.join(DAVAI_RC_DIR, 'bin')
    this_repo_bin = os.path.join(__this_repo__, 'bin')
    if os.path.islink(link) or os.path.exists(link):
        if os.path.islink(link) and os.readlink(link) == this_repo_bin:
            link = False
        else:
            overwrite = input("Relink '{}' to '{}' ? (y/n) : ".format(link, this_repo_bin)) in ('y', 'Y')
            if overwrite:
                os.unlink(link)
            else:
                link = None
            print("Warning: initialization might not be consistent with existing link !")
    if link:
        os.symlink(this_repo_bin, link)
        export_path = "export PATH=$PATH:{}\n".format(link)
        with io.open(DAVAI_PROFILE, 'a') as p:
            p.write(export_path)
    # User config
    preset_user_config_file()
    # Token
    if token:
        export_token_in_profile(token)
    # Profile
    bash_profile = os.path.join(os.environ['HOME'], '.bash_profile')
    with io.open(bash_profile, 'r') as b:
        sourced = any([DAVAI_PROFILE in l for l in b.readlines()])
    if not sourced:
        source = ['# DAVAI profile\n',
                  'if [ -f {} ]; then\n'.format(DAVAI_PROFILE),
                  '. {}\n'.format(DAVAI_PROFILE),
                  'fi\n',
                  '\n']
        with io.open(bash_profile, 'a') as b:
            b.writelines(source)
    print("------------------------------")
    print("DAVAI initialization completed. Re-login or source {} to finalize.".format(DAVAI_PROFILE))


def update(pull=False, token=None):
    """Update DAVAI-env and DAVAI-tests repositories using `git fetch`."""
    from .util import expandpath, export_token_in_profile  # import inside function because of circular dependency
    print("Update repo {} ...".format(__this_repo__))
    subprocess.check_call(['git', 'fetch', 'origin'], cwd=__this_repo__)
    if pull:
        subprocess.check_call(['git', 'pull', 'origin'], cwd=__this_repo__)
    if token:
        export_token_in_profile(token)
