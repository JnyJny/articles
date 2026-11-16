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

`audit` is advice, not a gate. It exits 0 unless you pass `--strict`, and
some of what it reports is deliberate, such as the `int* p` counterexamples
in the pointers article.

## Development

```console
$ uv run poe qc
```

runs the tests, ruff and ty. The tests build small article repos in a
temporary directory, so they do not depend on the real articles.
