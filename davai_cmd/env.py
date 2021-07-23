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

davai_home = os.path.join(os.environ['HOME'], '.davairc')
this_repo = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
davai_tests = 'davai-tests'
this_repo_tests = os.path.join(this_repo, davai_tests)
davai_xp_counter = os.path.join(os.environ['HOME'], '.davairc', '.last_xp')
DAVAI_IAL_REPOSITORY = os.environ.get('DAVAI_IAL_REPOSITORY',
                                      os.path.join(os.environ.get('HOME'), 'repositories', 'arpifs'))

# config
general_config_file = os.path.join(this_repo, 'conf', 'general.ini')
general_config = configparser.ConfigParser()
general_config.read(general_config_file)
user_config_file = os.path.join(davai_home, 'user_config.ini')
user_config = configparser.ConfigParser()
if os.path.exists(user_config_file):
    user_config.read(user_config_file)

# defaults
def set_defaults():
    """Set defaults, actual defaults or from user config if present"""
    defaults = {}
    # XP directory
    XP_directory = os.path.join(os.environ['HOME'], 'davai', 'experiments')
    if 'davai' in user_config.sections():
        XP_directory = user_config['davai'].get('XP_directory', XP_directory)
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

defaults = set_defaults()


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

