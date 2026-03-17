Author: Erik O'Shaughnessy
Date: 30 Apr 2020

# Poetical Python Packaging Posthaste

No history lesson [this][1] [time][2], this will be a down-to-business
article on how to package code using [poetry][0]. You'll need `poetry`
installed, a working [`pip`][3] and be [DtP][4].

## Bring Forth Form Upon The Filesystem

Python packages are composed of files and files live in a filesystem, so
make those files a home:

```console
$ poetry new /path/to/project/foo
Created package foo in /path/to/project/foo
```

As you can see, the prospective modern Python package programmer must
endure a great deal of pernicious pain in pursuit of our profession.

Alright, I'll abandon my attempts at overly florid idiom and aspire to
communicate in the dulcet tones of a more modern mode. Ok with you dog?

## What Did We Get?

```console
$ cd /path/to/project/foo
$ tree .
.
├── foo
│   └── __init__.py
├── pyproject.toml
├── README.rst
└── tests
    ├── __init__.py
    └── test_foo.py
```

Right now, without writing a line of code, we've got a fully-functional
python package. It doesn't _do_ anything but it's the minimal set of
files that can be packaged and uploaded to [PyPI][5]. Oh sure, you
can follow this [tutorial][7] and make the files yourself or you could
use `poetry`.

If you aren't a fan of `poetry` right now, this isn't the article for you.

So let's upload this [MVP][8] package to PyPI and show our third grade
teachers that we did amount to something. First you need to [create an
account][6] on PyPI and record your credentials. Mine are... ah ah ah,
that would be telling. Never keep your credentials in files that are
version controlled.

Of course we don't want to pollute PyPI with a bunch of do-nothing
packages and they don't want that either. That's why PyPI makes the
[test][9] package index available. You can publish any kind of garbage
too the test repo and it get's flushed eventually.















[0]: poetry
[1]: guest-exploring-python-clis
[2]: guest-python-packaging
[3]: pip
[4]: Down to Program
[5]: https://pypi.org
[6]: https://pypi.org/account/register/
[7]: https://packaging.python.org/tutorials/packaging-projects/
[8]: minimum viable product
[9]: https://test/pypi.org
[10]: https://packaging.python.org/overview/
