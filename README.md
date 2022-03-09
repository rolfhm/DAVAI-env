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
3. initialize your DAVAI environment: `make init` (or `bin/davai-init`) ---
   Note that this will also clone the [DAVAI-tests](https://github.com/ACCORD-NWP/DAVAI-tests) repository 
4. `export PATH=$PATH:~/.davairc/bin`
   (preferably in your `.bash_profile`)

* Local complements:
  * [`belenos`@MF](doc/belenos.md)

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
   based on `CY48T2` and comparing results to a reference being `CY48T2`:\
   `davai-prep_xp <IAL_git_reference> -v DV48T2 [-h]`\
   You may need to specify the path to your IAL repository by argument.
2. go to the displayed directory of the experiment (ending with `.../dv-xxxx@user/davai/nrv/`)
3. run the tests: `./RUN_XP.sh`\
   This script runs the 3 subscripts `0.setup_ciboulai.sh`, `1.packbuild.sh`, `2.tests.sh` in a sequence.
   * `0.setup_ciboulai.sh` (re-)initializes the current experiment in the *Ciboulai* dashboard.
   * `1.packbuild.sh` prepares a *gmkpack* pack with the source code of the provided Git reference, compiles the sources
     and build executables.
   * `2.tests.sh` runs the tests in semi-parallel, through job scheduler.

First tips
----------

* If the pack preparation or compilation fails, for whatever reason, the `1.packbuild.sh` prints an error message and
  the `RUN_XP.sh` stops before running the tests. You can find the output of the pack prep or compilation in `logs/`
  subdirectory, as any other test log.
* The tests are organised as *tasks* and *jobs*:
  * a *task* consists in fetching input resources, running an executable, analyzing its outputs to the Ciboulai dashboard
     and dispatching (archiving) them : *1 test = 1 task*
  * a *job* consists in a sequential driver of one or several *task(s)*: either a flow sequence (i.e. outputs of
     task N is an input of task N+1) or family sequence (e.g. run independantly an IFS and an Arpege forecast)
* To fix a piece of code, the best is to modify the code in your Git repo, then re-run `RUN_XP.sh` (or `1.packbuild.sh`
  and then `2.tests.sh`). You don't necessarily need to commit the change rightaway, the non-committed changes are 
  exported from Git to the pack. Don't forget to commit eventually though.
* To re-run a job after re-compilation, open `2.tests.sh`, find the `mkjob.py` command-line of the job, and run that command-line
  in interactive.
* Note: the `mkjob.py` argument `task=category.job` indicates that the job to be run is the driver in `./tasks/category/job.py`
* To re-run a single test within a job, e.g. the IFS forecast in `forecasts/standalone_forecasts.py` : edit this file,
  comment the other families or tasks (*nodes*) therein, and re-run the job as indicated above.
* Eventually after code modifications and fixing particular tests, you should re-run the whole set of tests, to make
  sure your fix does not break any other test.

By the way
----------

DAVAI means:

*"Dispositif d'Aide a la Validation d'Arpege-IFS & modeles a aire limitee"*

*"Device Aiming at the Validation of Arpege-IFS & limited area models"*

