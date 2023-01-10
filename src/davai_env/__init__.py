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
#DAVAI_PROFILE = os.path.join(DAVAI_RC_DIR, 'profile')
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


def initialize():
    """
    Initialize Davai env for user.
    """
    # import inside function because of circular dependency
    from .util import expandpath
    from .util import preset_user_config_file
    # Setup directories
    for d in ('davai_home', 'experiments', 'logs', 'default_mtooldir'):
        p = expandpath(config.get('paths', d))
        if os.path.exists(p):
            if not os.path.isdir(p):
                raise ValueError("config[paths][{}] is not a directory : '{}'".format(d, p))
        else:
            if '$' in p:
                raise ValueError("config[paths][{}] is not expandable : '{}'".format(d, p))
            os.makedirs(p)
    if not os.path.exists(DAVAI_RC_DIR):
        os.makedirs(DAVAI_RC_DIR)
    # User config
    preset_user_config_file()

# Make sure env is initialized at package import
initialize()
