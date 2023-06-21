Complementary information about DAVAI setup on `aa|ab|ac|ad` HPC machine @ ECMWF/Bologna
========================================================================================

Quick install
-------------

```
module load python3
module use ~rm9/public/modulefiles
module load davai
```
I advise to put the first two lines in your `.bash_profile`, and execute the third only when needed.

---

Pre-requirements (if not already set up)
----------------------------------------

1. Load modules (conveniently in your `.bash_profile`):
   ```
   module load python3
   module load ecmwf-toolbox/2021.08.3.0
   ```

2. Ensure permissions to `accord` group (e.g. with `chgrp`) for support
   ```
   for d in $HOME/davai $HOME/pack $SCRATCH/mtool
   do
   mkdir -p $d
   chgrp -R accord $d
   done
   ```

3. GMKPACK profile variables
   ```
   module load intel/2021.4.0
   
   # Gmkpack is installed at Ryad El Khatib's
   HOMEREK=~rme
   export GMKROOT=$HOMEREK/public/bin/gmkpack
   # use efficiently filesystems
   export ROOTPACK=$PERM/rootpack
   export HOMEPACK=$PERM/pack
   export GMKTMP=$TMPDIR/gmktmp
   # default compilation options
   export GMKFILE=OMPIIFC2104.AA
   export GMK_OPT=x
   # update paths
   export PATH=$GMKROOT/util:$PATH
   export MANPATH=$MANPATH:$GMKROOT/man
   ```
