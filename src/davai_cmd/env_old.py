#!/usr/bin/env python3
# -*- coding:Utf-8 -*-
"""
Davai API.
"""
from __future__ import print_function, absolute_import, unicode_literals, division

import os
import re
import configparser
import socket
import io
import copy

# fixed parameters
davai_rc = os.path.join(os.environ['HOME'], '.davairc')
davai_xp_counter = os.path.join(os.environ['HOME'], '.davairc', '.last_xp')

# repo
this_repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
davai_tests = 'davai-tests'
this_repo_tests = os.path.join(this_repo, 'src', davai_tests)

# config
general_config_file = os.path.join(this_repo, 'conf', 'general.ini')
general_config = configparser.ConfigParser()
general_config.read(general_config_file)
user_config_file = os.path.join(davai_rc, 'user_config.ini')
user_config = configparser.ConfigParser()
if os.path.exists(user_config_file):
    user_config.read(user_config_file)
config = copy.deepcopy(general_config)
if os.path.exists(user_config_file):
    config.read(user_config_file)


# defaults
def set_defaults():
    """Set defaults, actual defaults or from user config if present"""
    defaults = {}
    # DAVAI home
    davai_home = os.path.join(os.environ['HOME'], 'davai_home')
    if 'davai' in user_config.sections():
        davai_home = user_config['davai'].get('davai_home', davai_home)
    defaults['davai_home'] = davai_home
    defaults['XP_directory'] = os.path.abspath(os.path.expanduser(XP_directory))
    # logs directory
    _workdir = os.environ.get('WORKDIR', None)
    if _workdir:
        logs_directory = os.path.join(_workdir, 'davai', 'logs')
    else:
        logs_directory = os.path.join(os.environ['HOME'], 'davai', 'logs')
    if 'davai' in user_config.sections():
        logs_directory = user_config['davai'].get('logs_directory', logs_directory)
    defaults['logs_directory'] = os.path.abspath(os.path.expanduser(logs_directory))
    # usecase
    usecase = 'NRV'
    if 'davai' in user_config.sections():
        usecase = user_config['davai'].get('usecase', usecase)
    defaults['usecase'] = usecase
    return defaults


def possible_defaults_in_user_config():
    """Possible parameters which defaults that can be set in section [davai] of ~/.davairc/user_config.py"""
    print(list(defaults.keys()))


def guess_host():
    """
    Guess host from (by order of resolution):
      - $DAVAI_HOST
      - resolution from socket.gethostname() through:
        * $HOME/.davairc/user_config.ini
        * {davai_api install}/conf/general.ini
    """
    socket_hostname = socket.gethostname()
    host = os.environ.get('DAVAI_HOST', None)
    if not host:
        for config in (user_config, general_config):
            if 'hosts' in config.sections():
                for h, pattern in config['hosts'].items():
                    if re.match(pattern, socket_hostname):
                        host = h[:-len('_re_pattern')]  # h is '{host}_re_pattern'
                        break
                if host:
                    break
    if not host:
        raise ValueError("Couldn't find host in $DAVAI_HOST, " +
                         "nor guess from hostname ({}) and keys '{host}_re_pattern' " +
                         "in section 'hosts' of config files: ('{}', '{}')".format(
            socket_hostname, user_config_file, general_config_file))
    return host


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


def get_in_config(section, variable):
    """Get a variable from general/user config."""
    value = None
    for config in (user_config, general_config):
        if section in config.sections():
            if variable in config[section]:
                value = config[section][variable]
                break
    return value


def expandpath(path):
    return os.path.expanduser(os.path.expandvars(path))


def init():
    """
    Initialize Davai env for user.
    """
    # Setup home
    for d in ('home', 'experiments', 'logs'):
        p = expandpath(config.get('davai', d))
        if os.path.exists(p):
            if not os.path.isdir(p):
                raise ValueError("config[davai][{}] is not a directory : '{}'".format(d, p))
        else:
            if '$' in p:
                raise ValueError("config[davai][{}] is not expandable : '{}'".format(d, p))
            os.makedirs(p))
    # set rc
    if not os.path.exists(davai_rc):
        os.makedirs(davai_rc)
    # link repo (to have command line tools in PATH)
    link = os.path.join(davai_rc, 'davai')
    if os.path.exists(link):
        overwrite = input("Relink '{}' to '{}' ? (y/n) : ".format(link, this_repo)) in ('y', 'Y')
        if overwrite:
            os.unlink(link)
        else:
            link = None
            print("Warning: initialization might not be consistent with existing link !")
    if link:
        os.symlink(this_repo, link)
        print("To finalize setup, please export and/or copy to .bash_profile:")
        print("export PATH=$PATH:{}/bin".format(link))
    print("DAVAI initialization completed.")
    print("------------------------------")
