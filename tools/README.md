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
| `check`    | Runs `links`, `diagrams` and `layout`. Exits 1 on any problem.  |
| `links`    | Every link reference resolves: paths exist, anchors name headings. |
| `links --external` | Also fetches every external URL and reports the dead ones. |
| `diagrams` | Box dividers line up, and arrow elbows share a column.          |
| `layout`   | README symlinks work, and no article hides in a misnamed file.  |
| `audit`    | Counts findings per style rule. `--details` lists them.         |
| `stub`     | Creates the stub for a promised article.                        |

`audit` is advice, not a gate. It exits 0 unless you pass `--strict`.

## Promised articles

A link to an article that does not exist yet needs a stub, and a bare slug is
not a link. `stub` makes one: the directory, an `article.md` with a metadata
block marked `Status: stub`, a `README.md` symlink to it, and a Planned row in
the README.

```console
$ uv run article-tools stub c/data-types --title "What Is Data and Why Does It Need a Type?" \
      --note "how-i-write-main: main() returns a [signed integer]"
```

`--note` records where the article was promised, in a hidden comment, and can be
repeated. The slug must be kebab-case, the category one of `c`, `unix`, `python`
or `misc`, and an existing article is never overwritten. When `links` finds a
bare slug with no stub it prints this command.

## External links

`links --external` asks each external URL once, with HEAD and then GET. A 404 or
410 is a dead link and fails the command. Anything else that goes wrong, such as
a timeout or a 403 from a site that refuses bots, is reported as unreachable and
does not fail it. If a certificate cannot be verified the check asks again
without verifying and says so, because it only reads a status code.

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

## Hooks

The repo's `.pre-commit-config.yaml` runs `check` before every push, and this
tool's own tests and lint when anything under `tools/` changes. Hooks are not
versioned, so install them once in each clone:

```console
$ uvx pre-commit install --hook-type pre-commit --hook-type pre-push
```

`links --external` and `audit` are left out on purpose. The first needs the
network, and the second is advice until its remaining findings are cleaned up.

## Development

```console
$ uv run poe qc
```

runs the tests, ruff and ty. The tests build small article repos in a
temporary directory, so they do not depend on the real articles.
