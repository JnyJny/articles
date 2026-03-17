<!--
Author: Erik O'Shaughnessy
Editor: Johnny (Jny)
Date: April 2020 (revised March 2026)
Status: published
Series: Python
Prerequisites: none
Next: packaging-with-uv
-->

# Python Packaging Demystified

The next question from every new Python programmer, right after "how
do I print stuff," is:

"How do I make my awesome Python thingy available to other people?"

To answer that, we need to talk about the Python ecosystem and why
packaging matters. Not the mechanics -- we'll get to those in
separate articles on [uv][uv-article] and [Poetry][poetry-article].
This is about the _why_.

## Here Comes Another History Lesson

In the days of yore, when you needed a library to extend the
functionality of your program, you only had a few choices. You could
write it yourself. Your operating system might provide it. Or -- best
and worst of all -- you could look for it on the Internet.

Finding things on the early Internet was difficult. It took patience,
hard-won experience, and luck. You had to follow your favorite topic
in [USENET][usenet] news groups, exchange email with other developers,
hang out in [IRC][irc] chats, or hear about the latest thing while
hacking out your semester project in the computer lab. Later,
newfangled "web" servers started popping up using the untested and
weird [Hyper-Text Transfer Protocol][http]. These "websites" soon
proved their worth, becoming gateways to pre-existing but hard to find
anonymous [FTP][ftp] and [gopher][gopher] sites as well as aggregating
information on various esoteric topics.

If you found something close to what you needed, you then had to get
it running on your particular magic combination of hardware, compiler,
and operating system. The early Internet was not homogeneous -- there
were lots of different flavors of [Unix][unix], [VMS][vms],
[OS/2][os2], and many others now [forgotten][beos] running on just as
many different machines with varying architectures and capabilities.

The majority of software was written in C, which made porting easier
but far from simple. You had to work around different services offered
by different operating system flavors and different C compiler
implementations. Not to mention the different capabilities offered by
different hardware platforms -- not everybody had access to fancy new
CD-ROM drives and had to make do with 3.5" floppy disks.

After lots of hacking and learning far more about your machine, OS,
and compiler than you ever wanted, you finally have a compiled version
of the library that you hope works.

> "Testing? It compiled didn't it!? Ship it." - Embarrassingly, me.

You shim it into your project and get on with whatever it was you were
trying to accomplish. You can see why "roll your own" was a viable
option -- sometimes it was easier to just learn how to write the
functionality you needed than to find someone else's software and get
it running. That's how we got experts in cryptography, compression,
networking, languages, and all the other things that make computers
fun.

Finally, the nightmare scenario. Seven months later, after your
program has been put into production and you have moved on to another
project, a shadow falls across your desk. There's a bug and it stems
from the library you worked so hard to incorporate. You again have
choices: hope you can fix the library, hope the maintainer has fixed
the bug and the source is still accessible, or hope the Internet has
offered up a replacement in the interim.

Notice there is a lot of hoping there. Hope is not a plan.

## Why Python is Cooler Than Other Language Ecosystems

Python as a language is friendly to new programmers while providing
enough depth and mystique to draw in hard-core nerds. But the real
strength of Python isn't the language -- it's the ecosystem that
allows us to flippantly say "Oh, you need a high performance web
server for your new RESTful API? Just `pip install [gunicorn][gunicorn]`."

The discovery story has improved since the fun-old-days of trawling
USENET. [PyPI][pypi] (the Python Package Index) is the central
registry -- hundreds of thousands of packages, searchable, versioned,
and installable with a single command. The tooling has evolved too:
where we once had just `pip` and `setuptools`, we now have modern
tools like [Poetry][poetry] and [uv][uv] that handle dependency
resolution, virtual environments, and publishing in one coherent
workflow. Spoiler alert, uv is better than poetry post-2024. So you
time travellers take note and plan accordingly.

But beneath all the tooling, the foundational concept that makes the
magic possible is Python packaging -- the conventions and formats that
let us describe, build, distribute, and install Python code in a
predictable way. Understanding that foundation makes every tool you
pick up afterward make more sense.

## The Anatomy of a Package

A Python package is, at its simplest, a directory with a
`__init__.py` file in it. That's the signal to Python that "this
directory is importable." But a _distributable_ package -- one you
can share with the world -- needs a bit more structure. 

The turning point came with [PEP 518][pep-518], which introduced
`pyproject.toml` as a standard way to declare build requirements.
Before that, Python packaging was a maze of `setup.py` scripts that
had to import `setuptools` to declare that they depended on
`setuptools` -- a bootstrapping problem that made everyone miserable.
PEP 518 broke the cycle by giving projects a declarative file that
tools could read _before_ executing any Python code. Later,
[PEP 621][pep-621] standardized the `[project]` table for metadata,
so your project name, version, and dependencies all live in one
place regardless of which build tool you choose.

```
my-project
├── pyproject.toml
├── src
│   └── my_package
│       ├── __init__.py
│       └── core.py
└── tests
    └── test_core.py
```

The `pyproject.toml` file is where everything lives now: project
metadata, dependencies, build system configuration, tool settings.
It replaced the old `setup.py` / `setup.cfg` / `requirements.txt`
sprawl that confused everybody (including the tools).

A minimal `pyproject.toml` looks like:

```toml
[project]
name = "my-package"
version = "0.1.0"
description = "Does something useful, probably"
requires-python = ">=3.11"

dependencies = [
    "requests>=2.28",
]

[build-system]
requires = ["uv_build>=0.7,<0.8"]
build-backend = "uv_build"
```

This tells the packaging ecosystem everything it needs to know: what
your project is called, what Python version it needs, what it depends
on, and how to build it. The build backend (`uv_build`, `hatchling`,
`setuptools`, `flit`) is a choice you make once and rarely think
about again.

## Where To Go From Here

Now you know _why_ Python packaging exists and what problem it
solves. The next step is picking a tool and building something. We
have separate articles for the two modern approaches:

- [Packaging with uv][uv-article] -- the fast, Rust-powered newcomer
  that's eating everybody's lunch
- [Packaging with Poetry][poetry-article] -- the established,
  opinionated tool that got dependency management right

Pick one. Build a package. Put it on PyPI. The world is waiting for
your awesome Python thingy.

<!-- Links -->
[pep-518]: https://peps.python.org/pep-0518/
[pep-621]: https://peps.python.org/pep-0621/
[uv-article]: ../packaging-with-uv/article.md
[poetry-article]: ../packaging-with-poetry/article.md
[usenet]: https://en.wikipedia.org/wiki/Usenet
[irc]: https://en.wikipedia.org/wiki/IRC
[http]: https://en.wikipedia.org/wiki/HTTP
[ftp]: https://en.wikipedia.org/wiki/File_Transfer_Protocol
[gopher]: https://en.wikipedia.org/wiki/Gopher_(protocol)
[unix]: https://en.wikipedia.org/wiki/Unix
[vms]: https://en.wikipedia.org/wiki/OpenVMS
[os2]: https://en.wikipedia.org/wiki/OS/2
[beos]: https://en.wikipedia.org/wiki/BeOS
[gunicorn]: https://pypi.org/project/gunicorn/
[pypi]: https://pypi.org
[uv]: https://docs.astral.sh/uv/
[poetry]: https://python-poetry.org/
