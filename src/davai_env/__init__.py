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
import copy

__version__ = '0.0.2'

# fixed parameters
davai_rc = os.path.join(os.environ['HOME'], '.davairc')
davai_xp_counter = os.path.join(os.environ['HOME'], '.davairc', '.last_xp')

# repo
this_repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
davai_tests = 'davai-tests'
this_repo_tests = os.path.join(this_repo, davai_tests)

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
        raise ValueError("Couldn't find 'host' in [hosts] section of config files ('{}', '{}'), " +
                         "nor guess from hostname ({}) and keys '*host*_re_pattern' " +
                         "in section 'hosts' of same config files.".format(
            user_config_file, base_config_file, socket_hostname))
    return host

# config
base_config_file = os.path.join(this_repo, 'conf', 'base.ini')
user_config_file = os.path.join(davai_rc, 'user_config.ini')
config = configparser.ConfigParser()
config.read(base_config_file)
# read user config a first time to help guessing host
if os.path.exists(user_config_file):
    config.read(user_config_file)
# then complete config with host config file
host_config_file = os.path.join(this_repo, 'conf', '{}.ini'.format(guess_host()))
if os.path.exists(host_config_file):
    config.read(host_config_file)
# and read again user config so that it overwrites host config
if os.path.exists(user_config_file):
    config.read(user_config_file)


def next_xp_num():
    """Get number of next Experiment."""
    if not os.path.exists(davai_xp_counter):
        num = 0
    else:
        with open(davai_xp_counter, 'r') as f:
            num = int(f.readline())
    next_num = num + 1
    with open(davai_xp_counter, 'w') as f:
        f.write(str(next_num))
    return next_num


def expandpath(path):
    return os.path.expanduser(os.path.expandvars(path))


def init():
    """
    Initialize Davai env for user.
    """
    # Setup home
    for d in ('davai_home', 'experiments', 'logs'):
        p = expandpath(config.get('paths', d))
        if os.path.exists(p):
            if not os.path.isdir(p):
                raise ValueError("config[paths][{}] is not a directory : '{}'".format(d, p))
        else:
            if '$' in p:
                raise ValueError("config[paths][{}] is not expandable : '{}'".format(d, p))
            os.makedirs(p)
    # set rc
    if not os.path.exists(davai_rc):
        os.makedirs(davai_rc)
    # link repo (to have command line tools in PATH)
    link = os.path.join(davai_rc, 'bin')
    this_repo_bin = os.path.join(this_repo, 'bin')
    if os.path.exists(link):
        overwrite = input("Relink '{}' to '{}' ? (y/n) : ".format(link, this_repo_bin)) in ('y', 'Y')
        if overwrite:
            os.unlink(link)
        else:
            link = None
            print("Warning: initialization might not be consistent with existing link !")
    if link:
        os.symlink(this_repo_bin, link)
        print("To finalize setup, please export and/or copy to .bash_profile:")
        print("export PATH=$PATH:{}".format(link))
    print("DAVAI initialization completed.")
    print("------------------------------")
