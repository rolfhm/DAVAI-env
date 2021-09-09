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
import getpass
import shutil
import io
import re
import subprocess

from . import this_repo_tests, config
from . import guess_host, next_xp_num, expandpath


class AnXP(object):
    """Setup an XP."""

    def __init__(self, IAL_git_ref,
                 tests_version,
                 IAL_repository=config['paths']['IAL_repository'],
                 usecase=config['defaults']['usecase'],
                 ref_xpid='NONE',
                 comment=None,
                 host=guess_host()):
        """
        Initialize an XP.

        :param IAL_git_ref: the IFS-Arpege-LAM git reference to be tested
        :param tests_version: version of the test bench to be used
        :param usecase: among NRV, ELP, PC, ...
        :param IAL_repository: path to the IAL repository in which to get **IAL_git_ref** sources
        :param comment: descriptive comment for the experiment (defaults to **IAL_git_ref**)
        :param host: name of host machine, to link necessary packages and get according config file
            (otherwise guessed)
        :param dev_mode: to link tasks sources rather than to copy them
        """
        # initialisations
        self.IAL_git_ref = IAL_git_ref
        self.IAL_repository = IAL_repository
        self.tests_version = tests_version
        assert usecase in ('NRV', 'ELP'), "Usecase not implemented yet: " + usecase
        self.usecase = usecase
        self.xpid = '{:04}-{}@{}'.format(next_xp_num(), IAL_git_ref, getpass.getuser())
        self.ref_xpid = self.xpid if ref_xpid == 'SELF' else ref_xpid
        self.comment = comment if comment is not None else IAL_git_ref
        self.vconf = usecase.lower()
        self.host = host
        self.XP_path = os.path.join(expandpath(config['paths']['experiments']),
                                    self.xpid, 'davai', self.vconf)
        self.logs_directory = expandpath(config['paths']['logs'])
        self.packages = {p:config['packages'][p] for p in config['packages']}
        # dev mode links tasks/runs to modify them easily, but is dangerous cause they may be switched later on !
        self.dev_mode = os.environ.get('DAVAI_DEV_MODE', False) == '1'

    @property
    def host_XP_config_file(self):
        """Relative path of XP config file, according to host."""
        return os.path.join(this_repo_tests, 'conf', '{}.ini'.format(self.host))

    @property
    def XP_config_file(self):
        """Relative path of local XP config file."""
        return os.path.join('conf', 'davai_{}.ini'.format(self.vconf))

    def setup(self):
        """Setup the XP."""
        self._set_XP_path()
        self._set_conf()
        self._set_tasks()
        self._set_runs()
        self._link_packages()
        self._link_logs()
        self._end_of_setup_prompt()

    def _set_XP_path(self):
        if os.path.exists(self.XP_path):
            raise FileExistsError("XP path: '{}' already exists".format(self.XP_path))
        else:
            os.makedirs(self.XP_path)
            os.chdir(self.XP_path)

    def _set(self, source, target):
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
        # Switch to required version of the tests
        branches = subprocess.check_output(['git', 'branch'],
                                           cwd=this_repo_tests, stderr=None).decode('utf-8').split('\n')
        head = [line.strip() for line in branches if line.startswith('*')][0][2:]
        if head != self.tests_version:
            print("Switch davai-tests repo from current '{}' to tests_version '{}'".format(
                head, self.tests_version))
            try:
                subprocess.check_call(['git', 'checkout', 'origin/{}'.format(self.tests_version)], cwd=this_repo_tests)
                # FIXME: what about tags and/or commits ?
            except subprocess.CalledProcessError:
                print("Have you updated your davai-tests repository (command: davai-update) ?")
                raise
        # and copy/link
        self._set(os.path.join(this_repo_tests, 'src', 'tasks'),
                  'tasks')

    def _set_conf(self):
        """Copy and update XP config file."""
        # initialize
        os.makedirs('conf')
        shutil.copy(self.host_XP_config_file,
                    self.XP_config_file)
        to_set_in_config = {k:getattr(self, k)
                            for k in
                            ('IAL_git_ref', 'IAL_repository', 'usecase', 'comment', 'ref_xpid')}
        # and replace:
        print("Config setting ({}/{}) :".format(self.xpid, self.XP_config_file))
        # (here we do not use ConfigParser to keep the comments)
        with io.open(self.XP_config_file, 'r') as f:
            config = f.readlines()
        for i, line in enumerate(config):
            if line[0] not in (' ', '#', '['):  # special lines
                for k, v in to_set_in_config.items():
                    if k == 'IAL_repository': v = expandpath(v)
                    pattern = '(?P<k>{}\s*=).*\n'.format(k)
                    match = re.match(pattern, line)
                    if match:
                        config[i] = match.group('k') + ' {}\n'.format(v)
                        print(" -> {}".format(config[i].strip()))
        with io.open(self.XP_config_file, 'w') as f:
            f.writelines(config)

    def _set_runs(self):
        """Set run-wrapping scripts."""
        for r in ('RUN_XP.sh', '1.setup_ciboulai.sh', '2.packbuild.sh'):
            self._set(os.path.join(this_repo_tests, 'src', 'runs', r), r)
        self._set(os.path.join(this_repo_tests, 'src', 'runs', '{}_tests.sh'.format(self.usecase)),
                  '3.tests.sh')

    def _link_packages(self):
        """Link necessary packages in XP."""
        os.symlink(os.path.join(this_repo_tests, 'src', 'davai_taskutil'), 'davai_taskutil')
        for package, path in self.packages.items():
            os.symlink(expandpath(path), package)

    def _link_logs(self):
        """Link a 'logs' directory."""
        logs = os.path.join(self.logs_directory, self.xpid)
        if not os.path.exists(logs):
            os.makedirs(logs)
        os.symlink(logs, 'logs')

    def _end_of_setup_prompt(self):
        print("------------------------------------")
        print("DAVAI xp has been successfully setup:")
        print("* XPID:", self.xpid)
        print("* XP path:", self.XP_path)
        print("=> Now go to the XP path above and:")
        print("* if necessary, tune experiment in {}".format(self.XP_config_file))
        print("* launch using: ./run.sh")
        print("------------------------------------")
