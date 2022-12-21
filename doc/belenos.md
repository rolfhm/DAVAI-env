Complementary information about DAVAI on `belenos` HPC machine @ MF
===================================================================

Installation
------------

1. Load modules (conveniently in your `.bash_profile`):\
   `module load python/3.7.6`\
   `module load git`
2. Configure your ~/.netrc file for FTP communications with archive machine hendrix, if not already done:\
   `machine hendrix login <your_user> password <your_password>`\
   `machine hendrix.meteo.fr login <your_user> password <your_password>`\
   (! don't forget to `chmod 600 ~/.netrc` if you are creating this file !)
3. Configure ftserv (information is stored encrypted in ~/.ftuas):\
   `ftmotpasse -h hendrix -u <your_user>`\
   (and give your actual password)\
   **AND**\
   `ftmotpasse -h hendrix.meteo.fr -u <your_user>`\
   (same)
4. Configure Git proxy certificate info (conveniently in your `.bash_profile`):\
   `export GIT_SSL_CAINFO=/opt/softs/certificats/proxy1.pem`
5. Ensure SSH connectivity between compute and transfer nodes, if not already done:\
   `cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys`

* Optional: with a version of tests prior to `DV48T1_op0.04-1`, you may also need `epygram`:

  - `~mary/public/EPyGrAM/stable/_install/setup_epygram.py -v`
  - then to avoid a matplotlib/display issue, set:\
    `backend : Agg`\
    in `~/.config/matplotlib/matplotlibrc`
