#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Handle a Davai experiment.
"""

from __future__ import print_function, absolute_import, division, unicode_literals
import six

import json
import sys
import os

from bronx.stdtypes import date

from .env import (this_repo, this_repo_tests, guess_host, general_config, user_config,
                  defaults, next_xp_num, DAVAI_IAL_REPOSITORY)


class AnXP(object):
    """Setup an XP."""

    def __init__(self, IAL_git_ref,
                 IAL_repository=DAVAI_IAL_REPOSITORY,
                 usecase=defaults['usecase'],
                 ref_xpid='NONE',
                 comment=None,
                 host=guess_host(),
                 XP_directory=defaults['XP_directory'],
                 logs_directory=defaults['logs_directory'],
                 dev_mode=False):
        """
        Initialize an XP.

        :param IAL_git_ref: the IFS-Arpege-LAM git reference to be tested
        :param usecase: among NRV, ELP, PC, ...
        :param IAL_repository: path to the IAL repository in which to get **IAL_git_ref** sources
        :param comment: descriptive comment for the experiment (defaults to **IAL_git_ref**)
        :param host: name of host machine, to link necessary packages and get according config file
            (otherwise guessed)
        :param XP_directory: to specify a directory in which to create experiment, different from the default one
            defined in user_config.ini
        :param logs_directory: path in which to store log files
        :param dev_mode: to link tasks sources rather than to copy them
        """
        # initialisations
        self.IAL_git_ref = IAL_git_ref
        self.IAL_repository = IAL_repository
        assert usecase in ('NRV', 'ELP'), "Usecase not implemented yet: " + usecase
        self.usecase = usecase
        self.xpid = '{:03}-{}@{}'.format(next_xp_num(), IAL_git_ref, getpass.getuser())
        self.ref_xpid = ref_xpid
        self.comment = comment if comment is not None else IAL_git_ref
        self.vconf = usecase.lower()
        self.host = host
        self.XP_path = os.path.join(XP_directory, self.xpid, 'davai', self.vconf)
        self.logs_directory = logs_directory
        self.dev_mode = dev_mode  # dev mode links tasks/runs to modify them easily
        # packages
        self.packages = {}
        self.read_packages_from_config(general_config)
        self.read_packages_from_config(user_config)

    def read_packages_from_config(self, config):
        """Read packages location according to *host* from Davai config."""
        section = 'packages_' + self.host
        if section in config.sections():
            for k, v in config[section].items():
                self.packages[k] = v

    def setup(self):
        """Setup the XP."""
        if os.path.exists(self.XP_path):
            raise FileExistsError("XP path: '{}' already exists".format(self.XP_path))
        else:
            os.makedirs(self.XP_path)
            os.chdir(self.XP_path)
        self._set_conf()
        self._set_tasks()
        self._set_runs()
        self._link_packages()
        self._link_logs()
        print("------------------------------------")
        print("DAVAI xp has been successfully setup:")
        print("* XPID:", self.xpid)
        print("* XP path:", self.XP_path)
        print("------------------------------------")
        print("Now go to the XP path above and:")
        print("* if necessary, tune experiment in {}".format(self._XP_config_file))
        print("* launch using: ./run.sh")
        print("------------------------------------")

    def set(self, source, target):
        """Wrapper for copy/link depending on self.dev_mode."""
        if self.dev_mode:
            os.symlink(source, target)
        else:
            if os.path.isfile(source):
                shutil.copy(source, target)
            else:
                shutil.copytree(source, target)

    def _set_tasks(self):
        """Set tasks (templates)."""
        self.set(os.path.join(this_repo_tests, 'tasks'),
                 'tasks')

    @property
    def _host_XP_config_file(self):
        """Relative path of XP config file, according to host."""
        return os.path.join(this_repo_tests, 'conf', '{}.ini'.format(self.host))

    @property
    def _XP_config_file(self):
        """Relative path of local XP config file."""
        return os.path.join('conf', 'davai_{}.ini'.format(self.vconf))

    def _set_conf(self):
        """Copy and update XP config file."""
        # initialize
        os.makedirs('conf')
        shutil.copy(self._host_XP_config_file,
                    self._XP_config_file)
        to_set_in_config = {k:getattr(self, k)
                            for k in
                            ('IAL_git_ref', 'IAL_repository', 'usecase', 'comment', 'ref_xpid')}
        # and replace:
        # (here we do not use ConfigParser to keep the comments)
        with io.open(self._XP_config_file, 'r') as f:
            config = f.readlines()
        for i, line in enumerate(config):
            if line[0] not in (' ', '#', '['):  # special lines
                for k, v in to_set_in_config.items():
                    pattern = '(?P<k>{}\s*=).*\n'.format(k)
                    match = re.match(pattern, line)
                    if match:
                        config[i] = match.group('k') + ' {}\n'.format(v)
                        print(" -> is set in config: {}".format(config[i].strip()))
        with io.open(self._XP_config_file, 'w') as f:
            f.writelines(config)

    def _set_runs(self):
        """Set run-wrapping scripts."""
        for r in ('run.sh', 'setup_ciboulai.sh', 'packbuild.sh'):
            self.set(os.path.join(this_repo_tests, 'runs', r), r)
        self.set(os.path.join(this_repo_tests, 'runs', '{}_tests.sh'.format(self.usecase)),
                 'tests.sh')

    def _link_packages(self):
        """Link necessary packages in XP."""
        os.symlink(os.path.join(this_repo_tests, 'davai_taskutil'), 'davai_taskutil')
        for package, path in self.packages.items():
            os.symlink(path, package)

    def _link_logs(self):
        """Link a 'logs' directory."""
        logs = os.path.join(self.logs_directory, self.xpid)
        if not os.path.exists(logs):
            os.makedirs(logs)
        os.symlink(logs, 'logs')

