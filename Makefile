# Makefile - recursive build for articles
#
# Descends into directories containing Makefiles and invokes targets.
#
# Usage:
#   make render    - render all articles
#   make clean     - clean all articles

SUBDIRS := $(dir $(shell find . -mindepth 2 -name Makefile -not -path './.git/*'))

.PHONY: render clean list help $(SUBDIRS)

help: ## Show this help
	@echo "  render    Render all articles"
	@echo "  clean     Clean all articles"
	@echo "  list      Show article directories with Makefiles"

render: $(SUBDIRS) ## Render all articles
	@echo "Done."

clean: ## Clean all articles
	@for dir in $(SUBDIRS); do \
		$(MAKE) -C "$$dir" clean --no-print-directory; \
	done
	@echo "Cleaned."

list: ## Show article directories with Makefiles
	@for dir in $(SUBDIRS); do echo "  $$dir"; done

$(SUBDIRS):
	@$(MAKE) -C $@ render --no-print-directory
