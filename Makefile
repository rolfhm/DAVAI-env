# Variables

DOC_DIR         = doc/src
CLEANDIRS       = $(SUBDIRS:%=clean-%)

all: clean

.PHONY: all clean doc $(CLEANDIRS)

# TARGETS
doc:
	$(MAKE) -C $(DOC_DIR) doc

clean:
	find . -name "*.pyc"       -print0 | xargs -0r rm
	find . -name "__pycache__" -print0 | xargs -0r rm -r
	$(MAKE) -C $(DOC_DIR) clean

$(CLEANDIRS):
	$(MAKE) -C $(@:clean-%=%) clean

# Usual target
clobber: clean
