# article-tools

Checks for the articles repo: that every link goes somewhere, that box
diagrams line up, and that the articles follow the rules in `STYLE.md`
that a script can check. It replaces the one-off scripts that used to do
the style sweep.

## Usage

Run it from anywhere inside the repo. It finds the repo by looking for
`STYLE.md`, or you can pass `--root`.

```console
$ cd tools
$ uv run article-tools check
$ uv run article-tools audit
$ uv run article-tools audit --details --rule avoid-words
```

| Command    | What it does                                                    |
|------------|-----------------------------------------------------------------|
| `check`    | Runs `links` and `diagrams`. Exits 1 on any problem.            |
| `links`    | Every link reference resolves: paths exist, anchors name headings. |
| `diagrams` | Box dividers line up, and arrow elbows share a column.          |
| `audit`    | Counts findings per style rule. `--details` lists them.         |

`audit` is advice, not a gate. It exits 0 unless you pass `--strict`.

## Accepting findings

Some findings are deliberate, such as the `int* p` counterexamples in the
pointers article. `tools/accepted.toml` lists the ones that have been looked
at and accepted, each with a reason, and `audit` skips them and says how many.

```console
$ uv run article-tools audit --accept --rule link-text
$ git diff tools/accepted.toml
```

`--accept` adds every new finding for the rules you name, so read the diff
before you commit it. An entry matches on article, rule, message and the text
of the line, so changing the line brings the finding back. When the finding is
gone the entry is reported as stale, and you can delete it. `--strict` exits 1
only for new findings, and `--no-baseline` shows everything.

## Development

```console
$ uv run poe qc
```

runs the tests, ruff and ty. The tests build small article repos in a
temporary directory, so they do not depend on the real articles.
