#%Module1.0

# path to DAVAI-env on belenos
set modroot ~mary/public/DAVAI-env

module-whatis "Environment module for DAVAI-env"
module-whatis "Cf. https://github.com/ACCORD-NWP/DAVAI-env"
module-whatis "Local installation: $modroot"

# pre-requisites
if { [module-info mode load] || [module-info mode switch2] } {
  puts stderr "davai requires: git, python"
}
prereq git
prereq python

set modulename [module-info name]
set fields [split $modulename "/"]
set pkg_name [lindex $fields 0]
set pkg_vers [lindex $fields end]

prepend-path PATH $modroot/$pkg_vers/bin
prepend-path PYTHONPATH $modroot/$pkg_vers/src

if { [module-info mode load] || [module-info mode switch2] } {
  puts stderr "Environment for DAVAI-env commands loaded"
}
