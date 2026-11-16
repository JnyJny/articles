# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog][keep-a-changelog], and this
project adheres to [Semantic Versioning][semver].

## [Unreleased]

### Added

- `check`, `links`, `diagrams` and `audit` commands.
- Link checks for bare slugs, missing files, broken anchors, undefined
  references and unclosed reference labels.
- Diagram checks for misaligned cell dividers and arrow elbows.
- Twenty-one style rules from `STYLE.md`.
- `tools/accepted.toml`, `audit --accept`, `--baseline` and `--no-baseline`:
  findings that have been looked at and accepted are skipped, and entries
  that no longer match anything are reported as stale.

<!-- Links -->
[keep-a-changelog]: https://keepachangelog.com/en/1.1.0/
[semver]: https://semver.org/spec/v2.0.0.html
