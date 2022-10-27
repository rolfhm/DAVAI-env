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

from . import config, DAVAI_TESTS_REPO, davai_xpid_syntax
from . import guess_host, next_xp_num, expandpath


class AnXP(object):
    """Setup an XP."""

    def __init__(self, IAL_git_ref,
                 tests_version,
                 IAL_repository=config['paths']['IAL_repository'],
                 usecase=config['defaults']['usecase'],
                 compiling_system=config['defaults']['compiling_system'],
                 ref_xpid=None,
                 comment=None,
                 host=guess_host(),
                 fly_conf_parameters=dict()):
        """
        Initialize an XP.

        :param IAL_git_ref: the IFS-Arpege-LAM git reference to be tested
        :param tests_version: version of the test bench to be used
        :param usecase: among NRV, ELP, PC, ...
        :param compiling_system: the compiling system to be used, e.g. 'gmkpack'
        :param IAL_repository: path to the IAL repository in which to get **IAL_git_ref** sources
        :param comment: descriptive comment for the experiment (defaults to **IAL_git_ref**)
        :param host: name of host machine, to link necessary packages and get according config file
            (otherwise guessed)
        :param fly_conf_parameters: a dict of parameters to be modified on the fly in XP conf file
        """
        # initialisations
        self.IAL_git_ref = IAL_git_ref
        self.IAL_repository = IAL_repository
        self.tests_version = tests_version
        assert usecase in ('NRV', 'ELP'), "Usecase not implemented yet: " + usecase
        self.usecase = usecase
        self.compiling_system = compiling_system
        self.fly_conf_parameters = fly_conf_parameters
        self.xpid = davai_xpid_syntax.format(xpid_num=next_xp_num(),
                                             host=host,
                                             user=getpass.getuser())
        self.ref_xpid = self.xpid if ref_xpid == 'SELF' else ref_xpid
        self.comment = comment if comment is not None else IAL_git_ref
        self.vconf = usecase.lower()
        self.host = host
        self.XP_path = self.XP_path_generator(self.xpid, self.vconf)
        self.logs_directory = expandpath(config['paths']['logs'])
        self.packages = {p:config['packages'][p] for p in config['packages']}
        # dev mode links tasks/runs to modify them easily, but is dangerous cause they may be switched later on !
        self.dev_mode = os.environ.get('DAVAI_DEV_MODE', False) == '1'

    @staticmethod
    def XP_path_generator(xpid, vconf):
        return os.path.join(expandpath(config['paths']['experiments']), xpid, 'davai', vconf)

    @property
    def host_XP_config_file(self):
        """Relative path of XP config file, according to host."""
        return os.path.join(DAVAI_TESTS_REPO, 'conf', '{}.ini'.format(self.host))

    @property
    def XP_config_file(self):
        """Relative path of local XP config file."""
        return os.path.join('conf', 'davai_{}.ini'.format(self.vconf))

    def setup(self, take_tests_version_from_remote='origin'):
        """
        Setup the XP.

        :param take_tests_version_from_remote: to pick tests version from a remote in case of a branch
            None, False or '' to pick local branch
        """
        self._set_XP_path()
        self._set_conf()
        self._set_tasks(take_from_remote=take_tests_version_from_remote)
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

    @classmethod
    def set_tests_version(cls, gitref, take_from_remote='origin'):
        """Check that requested tests version exists, and switch to it."""
        remote_gitref = '{}/{}'.format(take_from_remote, gitref)
        branches = subprocess.check_output(['git', 'branch'],
                                           cwd=DAVAI_TESTS_REPO, stderr=None).decode('utf-8').split('\n')
        head = [line.strip() for line in branches if line.startswith('*')][0][2:]
        detached = re.match('\(HEAD detached at (?P<ref>.*)\)$', head)
        if detached:
            head = detached.group('ref')
        if (head != gitref and head != remote_gitref) or (head == gitref and take_from_remote):
            # determine if required tests version is a branch or not
            try:
                # A: is it a local branch ?
                cmd = ['git', 'show-ref', '--verify', 'refs/heads/{}'.format(gitref)]
                subprocess.check_call(cmd,
                                      cwd=DAVAI_TESTS_REPO,
                                      stderr=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                # A.no
                print("'{}' is not known in refs/heads/".format(gitref))
                # B: maybe it is a remote branch ?
                if take_from_remote:
                    cmd = ['git', 'show-ref', '--verify', 'refs/remotes/{}/{}'.format(take_from_remote, gitref)]
                    try:
                        subprocess.check_call(cmd,
                                              cwd=DAVAI_TESTS_REPO,
                                              stderr=subprocess.DEVNULL,
                                              stdout=subprocess.DEVNULL)
                    except subprocess.CalledProcessError:
                        # B.no: so either it is tag/commit, or doesn't exist, nothing to do about remote
                        print("'{}' is not known in refs/remotes/{}".format(gitref, take_from_remote))
                    else:
                        # B.yes: remote branch only
                        gitref = remote_gitref
                        print("'{}' taken from remote '{}'".format(gitref, take_from_remote))
            else:
                # A.yes: this is a local branch, do we take it from remote or local ?
                if take_from_remote:
                    gitref = remote_gitref
            # remote question has been sorted
            print("Switch DAVAI-tests repo from current HEAD '{}' to '{}'".format(head, gitref))
            try:
                subprocess.check_call(['git', 'checkout', gitref], cwd=DAVAI_TESTS_REPO)
            except subprocess.CalledProcessError:
                print("Have you updated your DAVAI-tests repository (command: davai-update) ?")
                raise

    def _set_tasks(self, take_from_remote='origin'):
        """Set tasks (templates)."""
        self.set_tests_version(self.tests_version, take_from_remote=take_from_remote)
        # and copy/link
        self._set(os.path.join(DAVAI_TESTS_REPO, 'src', 'tasks'),
                  'tasks')

    def _set_conf(self):
        """Copy and update XP config file."""
        # initialize
        os.makedirs('conf')
        shutil.copy(self.host_XP_config_file,
                    self.XP_config_file)
        to_set_in_config = {k:getattr(self, k)
                            for k in
                            ('IAL_git_ref', 'IAL_repository', 'usecase', 'comment', 'ref_xpid', 'compiling_system',
                             'tests_version')}
        to_set_in_config.update(self.fly_conf_parameters)
        # and replace:
        print("------------------------------------")
        print("Config setting ({}/{}) :".format(self.xpid, self.XP_config_file))
        # (here we do not use ConfigParser to keep the comments)
        with io.open(self.XP_config_file, 'r') as f:
            config = f.readlines()
        for i, line in enumerate(config):
            if line[0] not in (' ', '#', '['):  # special lines
                for k, v in to_set_in_config.items():
                    if k == 'IAL_repository': v = expandpath(v)
                    pattern = '^(?P<k>{}\s*=).*\n'.format(k)
                    match = re.match(pattern, line)
                    if match and v is not None:
                        config[i] = match.group('k') + ' {}\n'.format(v)
                        print(" -> {}".format(config[i].strip()))
        with io.open(self.XP_config_file, 'w') as f:
            f.writelines(config)
        print("------------------------------------")

    def _set_runs(self):
        """Set run-wrapping scripts."""
        runs = ['RUN_XP.sh', '0.setup_ciboulai.sh', '2.tests.sh']
        if self.usecase in ('NRV', 'ELP'):
            runs.append('2.NRV_tests.sh')
            if self.usecase == 'ELP':
                runs.append('2.ELP_tests.sh')
        for r in runs:
            self._set(os.path.join(DAVAI_TESTS_REPO, 'src', 'runs', r), r)
        self._set(os.path.join(DAVAI_TESTS_REPO, 'src', 'runs', '1.{}_build.sh'.format(self.compiling_system)),
                  '1.build.sh')

    def _link_packages(self):
        """Link necessary packages in XP."""
        os.symlink(os.path.join(DAVAI_TESTS_REPO, 'src', 'davai_taskutil'), 'davai_taskutil')
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
        print("* launch using: ./RUN_XP.sh")
        print("------------------------------------")
