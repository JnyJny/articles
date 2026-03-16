# Makefile - render mermaid diagrams in article markdown files
#
# Usage:
#   make diagrams    - render all mermaid blocks to SVG
#   make clean       - remove generated SVG files
#   make list        - show articles containing mermaid blocks
#
# Requirements: Node.js (npx handles the rest)

MMDC := npx --yes @mermaid-js/mermaid-cli
MMDC_FLAGS := --backgroundColor transparent --theme neutral

# Find all article.md files containing mermaid code blocks
ARTICLES := $(shell grep -rl '```mermaid' --include='*.md' . 2>/dev/null)

# Directory for extracted .mmd files
BUILD := .build

.PHONY: diagrams clean list help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

diagrams: ## Render all mermaid diagrams to SVG
	@mkdir -p $(BUILD)
	@for article in $(ARTICLES); do \
		dir=$$(dirname "$$article"); \
		base=$$(basename "$$dir"); \
		echo "Processing: $$article"; \
		python3 -c "\
import sys, re, pathlib; \
text = pathlib.Path(sys.argv[1]).read_text(); \
blocks = re.findall(r'\`\`\`mermaid\n(.*?)\n\`\`\`', text, re.DOTALL); \
[pathlib.Path(f'$(BUILD)/$$base-{i+1}.mmd').write_text(b) for i, b in enumerate(blocks)]; \
print(f'  Extracted {len(blocks)} diagrams')" "$$article"; \
		for mmd in $(BUILD)/$$base-*.mmd; do \
			[ -f "$$mmd" ] || continue; \
			svg="$$dir/$$(basename "$$mmd" .mmd).svg"; \
			echo "  Rendering: $$(basename $$mmd) -> $$svg"; \
			$(MMDC) $(MMDC_FLAGS) -i "$$mmd" -o "$$svg" 2>/dev/null; \
		done; \
	done
	@rm -rf $(BUILD)
	@echo "Done."

clean: ## Remove generated diagram files
	@find . -name '*-[0-9]*.svg' -not -path './.git/*' -delete 2>/dev/null || true
	@find . -name '*-[0-9]*.png' -not -path './.git/*' -delete 2>/dev/null || true
	@rm -rf $(BUILD)
	@echo "Cleaned."

list: ## Show articles containing mermaid blocks
	@if [ -z "$(ARTICLES)" ]; then \
		echo "No articles with mermaid diagrams found."; \
	else \
		for article in $(ARTICLES); do \
			count=$$(grep -c '```mermaid' "$$article"); \
			echo "  $$article ($$count diagrams)"; \
		done; \
	fi
