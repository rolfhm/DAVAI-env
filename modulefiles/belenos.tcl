#%Module1.0

# path to DAVAI-env on belenos
set modroot ~mary/public/DAVAI-env

set modulename [module-info name]
set fields [split $modulename "/"]
set pkg_name [lindex $fields 0]
set pkg_vers [lindex $fields end]

prepend-path PATH $modroot/$pkg_vers/bin
prepend-path PYTHONPATH $modroot/$pkg_vers/src
