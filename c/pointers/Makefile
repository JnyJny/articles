# Makefile - render mermaid diagrams for this article
#
# Requirements: Node.js (npx handles the rest)

MMDC := npx --yes @mermaid-js/mermaid-cli
MMDC_FLAGS := --backgroundColor transparent --theme neutral
ARTICLE := article.md
BUILD := .build
SVGS :=

.PHONY: render clean help

help: ## Show this help
	@echo "  render    Extract and render mermaid diagrams to SVG"
	@echo "  clean     Remove generated SVG files"

render: ## Render mermaid diagrams to SVG
	@mkdir -p $(BUILD)
	@python3 -c "\
import re, pathlib; \
text = pathlib.Path('$(ARTICLE)').read_text(); \
blocks = re.findall(r'\`\`\`mermaid\n(.*?)\n\`\`\`', text, re.DOTALL); \
[pathlib.Path('$(BUILD)/diagram-{}.mmd'.format(i+1)).write_text(b) for i, b in enumerate(blocks)]; \
print('  Extracted {} diagrams'.format(len(blocks)))"
	@for mmd in $(BUILD)/diagram-*.mmd; do \
		[ -f "$$mmd" ] || continue; \
		svg="$$(basename "$$mmd" .mmd).svg"; \
		echo "  Rendering: $$svg"; \
		$(MMDC) $(MMDC_FLAGS) -i "$$mmd" -o "$$svg" 2>/dev/null; \
	done
	@rm -rf $(BUILD)

clean: ## Remove generated files
	@rm -f diagram-*.svg
	@rm -rf $(BUILD)
