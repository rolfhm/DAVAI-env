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

By the way
----------

DAVAI means:

*"Dispositif d'Aide a la Validation d'Arpege-IFS & modeles a aire limitee"*

*"Device Aiming at the Validation of Arpege-IFS & limited area models"*

