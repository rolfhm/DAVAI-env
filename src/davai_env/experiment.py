#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Handle a Davai experiment.
"""

from __future__ import print_function, absolute_import, division, unicode_literals
import six

import sys
import os
import getpass
import io
import re
import subprocess
import configparser
import yaml
import time

from . import config, davai_xpid_syntax, set_default_mtooldir, guess_host, next_xp_num, expandpath


def vconf2usecase(vconf):
    return vconf.upper()

def usecase2vconf(usecase):
    return usecase.lower()


class XPmaker(object):

    experiments_rootdir = expandpath(config['paths']['experiments'])

    @staticmethod
    def _new_XPID(host):
        return davai_xpid_syntax.format(xpid_num=next_xp_num(),
                                        host=host,
                                        user=getpass.getuser())

    @classmethod
    def _new_XP_path(cls, host, usecase):
        return os.path.join(cls.experiments_rootdir, cls._new_XPID(host), 'davai', usecase2vconf(usecase))

    @staticmethod
    def _setup_XP_path(xp_path):
        assert not os.path.exists(xp_path), "XP path: '{}' already exists".format(xp_path)
        os.makedirs(xp_path)
        print("XP path created : {}".format(xp_path))

    @classmethod
    def new_xp(cls, davai_tests_version, particular_config,
               davai_tests_remote=config['defaults']['davai_tests_origin'],
               usecase=config['defaults']['usecase'],
               host=guess_host()):

        assert usecase in ('NRV', 'ELP'), "Usecase not implemented yet: " + usecase
        xp_path = cls._new_XP_path(host, usecase)
        cls._setup_XP_path(xp_path)
        # now XP path is created, we move in for the continuation of the experiment setup
        os.chdir(xp_path)
        xp = ThisXP(new=True)
        xp.setup(davai_tests_version, particular_config,
                 davai_tests_remote=davai_tests_remote,
                 usecase=usecase,
                 host=host)
        return xp


class ThisXP(object):
    """Handles the existing experiment determined by the current working directory."""

    davai_tests_dir = 'DAVAI-tests'
    particular_config_file = os.path.join('conf', 'this_xp.yaml')

    def __init__(self, new=False):
        self.xp_path = os.getcwd()
        self.xpid = os.path.basename(os.path.dirname(os.path.dirname(self.xp_path)))
        self.vapp = os.path.basename(os.path.dirname(self.xp_path))
        self.vconf = os.path.basename(self.xp_path)
        self.usecase = vconf2usecase(self.vconf)
        self.general_config_file = os.path.join('conf','{}_{}.ini'.format(self.vapp, self.vconf))
        if not new:
            self.assert_cwd_is_an_xp()

# setup --------------------------------------------------------------------------------------------------------------

    def setup(self, davai_tests_version, particular_config,
              davai_tests_remote=config['defaults']['davai_tests_origin'],
              usecase=config['defaults']['usecase'],
              host=guess_host()):
        """Setup the experiment (at creation time)."""
        # set DAVAI-tests repo
        self._setup_DAVAI_tests(davai_tests_remote, davai_tests_version)
        self._setup_tasks()
        self._setup_packages()
        self._setup_logs()
        # configuration files
        os.makedirs('conf')
        self._setup_conf_particular(particular_config)
        self._setup_conf_usecase(usecase)
        self._setup_conf_general(host)
        self._setup_final_prompt()

    @staticmethod
    def _checkout_davai_tests(gitref):
        """Check that requested tests version exists, and switch to it."""
        remote = 'origin'
        remote_gitref = '{}/{}'.format(remote, gitref)
        branches = subprocess.check_output(['git', 'branch'], stderr=None).decode('utf-8').split('\n')
        head = [line.strip() for line in branches if line.startswith('*')][0][2:]
        detached = re.match('\(HEAD detached at (?P<ref>.*)\)$', head)
        if detached:
            head = detached.group('ref')
        if (head != gitref and head != remote_gitref) or (head == gitref and remote):
            # determine if required tests version is a branch or not
            try:
                # A: is it a local branch ?
                cmd = ['git', 'show-ref', '--verify', 'refs/heads/{}'.format(gitref)]
                subprocess.check_call(cmd,
                                      stderr=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                # A.no
                print("'{}' is not known in refs/heads/".format(gitref))
                # B: maybe it is a remote branch ?
                cmd = ['git', 'show-ref', '--verify', 'refs/remotes/{}/{}'.format(remote, gitref)]
                try:
                    subprocess.check_call(cmd,
                                          stderr=subprocess.DEVNULL,
                                          stdout=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    # B.no: so either it is tag/commit, or doesn't exist, nothing to do about remote
                    print("'{}' is not known in refs/remotes/{}".format(gitref, remote))
                else:
                    # B.yes: remote branch only                        gitref = remote_gitref
                    gitref = remote_gitref
                    print("'{}' taken from remote '{}'".format(gitref, remote))
            else:
                # A.yes: this is a local branch, do we take it from remote or local ?
                gitref = remote_gitref
            # remote question has been sorted
            print("Switch DAVAI-tests repo from current HEAD '{}' to '{}'".format(head, gitref))
            try:
                subprocess.check_call(['git', 'checkout', gitref, '-q'])
            except subprocess.CalledProcessError:
                print("Have you updated your DAVAI-tests repository (command: davai-update) ?")
                raise

    def _setup_DAVAI_tests(self, remote, version):
        """Clone and checkout required version of the DAVAI-tests."""
        subprocess.check_call(['git', 'clone', remote, self.davai_tests_dir])
        os.chdir(self.davai_tests_dir)
        subprocess.check_call(['git', 'fetch', 'origin', version, '-q'])
        #subprocess.check_call(['git', 'checkout', '-t', 'origin/{}'.format(version)])
        self._checkout_davai_tests(version)
        os.chdir(self.xp_path)

    def _setup_conf_particular(self, particular_config):
        """Particular config: parameters meant to vary from one XP to another, and not version controlled."""
        # complete particular config
        if particular_config.get('comment', None) is None:
            particular_config['comment'] = particular_config['IAL_git_ref']
        repo = particular_config.get('IAL_repository', config['paths']['IAL_repository'])
        particular_config['IAL_repository'] = expandpath(repo)
        with io.open(self.particular_config_file, 'w') as f:
            yaml.dump(particular_config, f)

    def _setup_conf_usecase(self, usecase):
        """Usecase config : set of jobs/tests."""
        filename = os.path.join('conf', '{}.yaml'.format(self.usecase))
        os.symlink(os.path.join('..', self.davai_tests_dir, filename),
                   filename)

    def _setup_conf_general(self, host=guess_host()):
        """General config file for the jobs."""
        host_general_config_file = os.path.join(self.davai_tests_dir, 'conf', '{}.ini'.format(host))
        os.symlink(host_general_config_file,
                   self.general_config_file)

    def _setup_tasks(self):
        """Link tasks."""
        os.symlink(os.path.join(self.davai_tests_dir, 'src', 'tasks'),
                   'tasks')

    def _setup_packages(self):
        """Link necessary packages in XP."""
        # davai_taskutil from DAVAI-tests locally checkedout
        os.symlink(os.path.join(self.davai_tests_dir, 'src', 'davai_taskutil'),
                   'davai_taskutil')
        # other packages
        packages = {p:expandpath(config['packages'][p]) for p in config['packages']}
        for package, path in packages.items():
            os.symlink(expandpath(path), package)

    def _setup_logs(self):
        """Deport 'logs' directory."""
        logs_directory = expandpath(config['paths']['logs'])
        logs = os.path.join(logs_directory, self.xpid)
        os.makedirs(logs)
        os.symlink(logs, 'logs')

    def _setup_final_prompt(self):
        """Final prompt for the setup of the experiment."""
        print("------------------------------------")
        print("DAVAI xp '{}' has been successfully setup !".format(self.xpid))
        print("Now go to the XP path below and:")
        print("- if necessary, tune experiment in '{}'".format(self.general_config_file))
        print("- run experiment using: 'davai-run_xp'")
        print("  =>", self.xp_path)
        print("------------------------------------")

    def write_genesis(self, command):
        """Write the command that created the XP in a .genesis file."""
        with io.open(os.path.join(self.xp_path, '.genesis'), 'w') as g:
            g.write(str(command))

# properties ----------------------------------------------------------------------------------------------------------

    def cwd_is_an_xp(self):
        """Whether the cwd is an actual experiment or not."""
        return os.path.exists(self.general_config_file)

    def assert_cwd_is_an_xp(self):
        """Assert that the cwd is an actual experiment."""
        assert self.cwd_is_an_xp(), "Current working directory is not a Davai experiment directory"

    @property
    def conf(self):
        if not hasattr(self, '_conf'):
            config = configparser.ConfigParser()
            config.read(self.general_config_file)
            self._conf = config
        return self._conf

    @property
    def particular_config(self):
        """Particular config: parameters meant to vary from one XP to another, and not version controlled."""
        if not hasattr(self, '_particular_config'):
            with io.open(self.particular_config_file, 'r') as f:
                self._particular_config = yaml.load(f, yaml.Loader)
        return self._particular_config

    @property
    def all_jobs(self):
        """Get all jobs according to *usecase* (found in config)."""
        if not hasattr(self, '_all_jobs'):
            jobs_list_file = 'conf/{}.yaml'.format(self.usecase)
            with io.open(jobs_list_file, 'r') as fin:
                self._all_jobs = yaml.load(fin, yaml.Loader)
        return self._all_jobs

    @property
    def davai_tests_version(self):
        cmd = ['git', 'log' , '-n1', '--decorate', '--oneline']
        output = subprocess.check_output(['git', 'log' , '-n1', '--decorate', '--oneline'],
                                         cwd=os.path.join(self.xp_path, self.davai_tests_dir)
                                         ).decode('utf-8').split('\n')
        return output[0]

# utilities ----------------------------------------------------------------------------------------------------------

    def print_jobs(self):
        """Print all jobs according to *usecase* (found in config)."""
        for family, jobs in self.all_jobs.items():
            for job in jobs:
                print('.'.join([family, job]))

    def _launch(self, task, name,
               drymode=False,
               **extra_parameters):
        """
        Launch one job.

        :param task: submodule of the driver to be executed, e.g. assim.BSM_4D_arpege
        :param name: name of the job, to get its confog characteristics (profile, ...)
        :param extra_parameters: extra parameters to be passed to mkjob on the fly
        """
        cmd = ['python3', 'vortex/bin/mkjob.py', '-j',
               'task={}'.format(task.strip()), 'name={}'.format(name.strip())]
        cmd.extend(['{}={}'.format(k,v) for k,v in extra_parameters.items()])
        print("Executing: '{}'".format(' '.join(cmd)))
        if not drymode:
            subprocess.check_call(cmd)

    def launch_ciboulai_init(self):
        """(Re-)Initialize Ciboulai dashboard."""
        self._launch('ciboulai_xpsetup', 'ciboulai_xpsetup',
                     profile='rd',
                     usecase=self.usecase,
                     tests_version=self.davai_tests_version,
                     **self.particular_config)

    def launch_build(self,
                     drymode=False,
                     preexisting_pack=False):
        """Launch build job."""
        os.environ['DAVAI_START_BUILD'] = str(time.time())
        if self.conf['DEFAULT']['compiling_system'] == 'gmkpack':
            if 'IAL_git_ref' in self.particular_config:
                # build from a single IAL Git reference
                assert 'IAL_repository' in self.particular_config
                self._launch('build.gmkpack.build_from_gitref', 'build',
                             drymode=drymode,
                             preexisting_pack=preexisting_pack,
                             IAL_repository=self.particular_config['IAL_repository'],
                             IAL_git_ref=self.particular_config['IAL_git_ref'])
            elif 'bundle' in self.particular_config or 'bundle_file' in self.particular_config:
                # build from a bundle
                raise NotImplementedError("Build from a bundle: not yet !")
            else:
                raise KeyError("Particular config should contain one of: ('IAL_git_ref', 'bundle', 'bundle_file')")
        else:
            raise NotImplementedError("compiling_system == {}".format(self.conf['DEFAULT']['compiling_system']))
        # run build monitoring
        set_default_mtooldir()
        self._launch('build.wait4build', 'build',
                     drymode=drymode,
                     profile='rd')

    def launch_jobs(self, only_job=None, drymode=False):
        """Launch jobs, either all, or only the one requested."""
        for family, jobs in self.all_jobs.items():
            for job in jobs:
                task = '.'.join([family, job])
                name = job
                if only_job in (None, task):
                    self._launch(task, name, drymode=drymode)

    def afterlaunch_prompt(self):
        print("=" * 100)
        print("=== {:^92} ===".format("DAVAI {} test bench launched through job scheduler !".format(self.usecase)))
        print("=== {:^92} ===".format("Checkout Ciboulai for results on: {}".format(self.conf['DEFAULT']['davai_server'])))
        print("=" * 100)

    def status(self, task=None):
        """Print status of tasks, read from cache files."""
        # First we need MTOOLDIR set up for retrieving paths
        set_default_mtooldir()
        # Then set Vortex in path
        vortexpath = expandpath(config['packages']['vortex'])
        sys.path.extend([vortexpath, os.path.join(vortexpath, 'src'), os.path.join(vortexpath, 'site')])
        # vortex/davai
        import vortex
        import davai
        # process stack or task
        stack = davai.util.SummariesStack(vortex.ticket(), self.vapp, self.vconf, self.xpid)
        if task is None:
            stack.tasks_status(print_it=True)
        else:
            stack.task_summary_fullpath(task)

