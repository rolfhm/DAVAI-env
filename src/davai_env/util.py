#!/usr/bin/env python3
# -*- coding:Utf-8 -*-
"""
Utilities.
"""
from __future__ import print_function, absolute_import, unicode_literals, division

import os
import io
import datetime

from . import config, DAVAI_XP_COUNTER, CONFIG_USER_FILE, CONFIG_TEMPLATE_USER_FILE


def expandpath(path):
    """Expand user and env var in a path)."""
    return os.path.expanduser(os.path.expandvars(path))

def next_xp_num():
    """Get number of next Experiment."""
    if not os.path.exists(DAVAI_XP_COUNTER):
        num = 0
    else:
        with io.open(DAVAI_XP_COUNTER, 'r') as f:
            num = int(f.readline())
    next_num = num + 1
    with io.open(DAVAI_XP_COUNTER, 'w') as f:
        f.write(str(next_num))
    return next_num

def default_mtooldir():
    """Return default MTOOLDIR from config."""
    MTOOLDIR = expandpath(config['paths'].get('default_mtooldir'))
    return MTOOLDIR

def set_default_mtooldir():
    """Set env var MTOOLDIR from config if not already in environment."""
    if not os.environ.get('MTOOLDIR', None):
        MTOOLDIR = default_mtooldir()
        if MTOOLDIR:
            os.environ['MTOOLDIR'] = MTOOLDIR

def export_token_in_profile(token):
    """Export Ciboulai token in davai profile."""
    from . import DAVAI_PROFILE
    with io.open(DAVAI_PROFILE, 'a') as p:
        p.write("export CIBOULAI_TOKEN={}  # update: {}\n".format(token, str(datetime.date.today())))

def vconf2usecase(vconf):
    """Convert vconf to usecase."""
    return vconf.upper()

def usecase2vconf(usecase):
    """Convert usecase to vconf."""
    return usecase.lower()

def preset_user_config_file(prompt=None):
    """Copy a (empty/commented) template of user config file."""
    if not os.path.exists(CONFIG_USER_FILE):
        with io.open(CONFIG_TEMPLATE_USER_FILE, 'r') as i:
            t = i.readlines()
        with io.open(CONFIG_USER_FILE, 'w') as o:
            for l in t:
                o.write('#' + l)
        prompt = True
    if prompt:
        print("See user config file to be tuned in : '{}'".format(CONFIG_USER_FILE))
