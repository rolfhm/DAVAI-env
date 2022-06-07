DAVAI environment & interface
=============================

This project contains:
* the DAVAI command-line tools, esp. to create DAVAI experiments,
* the configuration files to handle general preferences and machine-dependent installation,
* a tool for DAVAI developers to move shelves around,

Installation
------------

1. assert to have a recent version of git:
   (e.g. on belenos `module load git`)
2. clone this repository (`git clone https://github.com/ACCORD-NWP/DAVAI-env.git`)
3. initialize your DAVAI environment: `make init` (or `bin/davai-init`) | Note that this will also clone the DAVAI-tests
   repository (https://github.com/ACCORD-NWP/DAVAI-tests)
4. `export PATH=$PATH:~/.davairc/bin`
   (preferably in your `.bash_profile`)

Dependencies
------------

DAVAI tests require the following packages:
* `ial_build`: wrappers to build IAL executables
* `ial_expertise`: to analyse the outputs of the tests
* Vortex project and its sub-packages

These packages are already pre-installed on MF's HPC, nothing to do.

Get started
-----------

After installation, to run an experiment (pre-bundle version):

1. prepare an experiment based on version `DV48T2` of the tests, i.e. with a configuration of the tests suited for code
   based on `CY48T2` and comparing results to a reference being `CY48T2`:
   `davai-prep_xp <IAL_git_reference> -v DV48T2 [-h]`
   You may need to specify the path to your IAL repository by argument.
2. go to the displayed directory of the experiment (ending with `.../dv-xxxx@user/davai/nrv/`)
3. run the tests: `./RUN_XP.sh`
   This script runs the 3 subscripts `0.setup_ciboulai.sh`, `1.packbuild.sh`, `2.tests.sh` in a sequence.

* `0.setup_ciboulai.sh` (re-)initializes the current experiment in the *Ciboulai* dashboard.
* `1.packbuild.sh` prepares a *gmkpack* pack with the source code of the provided Git reference, compiles the sources
  and build executables.
* `2.tests.sh` runs the tests in semi-parallel, through job scheduler.

* If the pack preparation or compilation fails, for whatever reason, the `1.packbuild.sh` prints an error message and
  the `RUN_XP.sh` stops before running the tests. You can find the output of the pack prep or compilation in `logs/`
  subdirectory, as any other test log.

By the way
----------

DAVAI means:

*"Dispositif d'Aide a la Validation d'Arpege-IFS & modeles a aire limitee"*

*"Device Aiming at the Validation of Arpege-IFS & limited area models"*

