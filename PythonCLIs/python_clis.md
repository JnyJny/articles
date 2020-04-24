# An Exploration of Modern Python CLI and Packaging

The goal here is twofold: help the new developer learn how to create
and package their own command-line applications written in Python
and secondly why things are named and organized they way they are.

## In the Beginning...

First, some history about command-line driven design from a [UNIX][13]
persepective.

UNIX is a computer operating system and is the ancestor of Linux and
MacOS (and [many other operating systems][11] as well). The primary
language for developing programs under UNIX is [C][12], often called the
portable assembler.  C is the language that built the Internet and
most of the cool things that we rely on everyday: web browsers, web
servers, operating systems, DNS, TCP/IP, and nearly every other piece
of software that contributes to the ecosystem of today's Internet.

So it behooves us to at least understand the basics of a [C program][0] .

Assuming you didn't read that, the basic architecture of a C program
is a function called `main` whose signature looks like:

```C
   int main(int argc, char **argv) { ... }
```

This shouldn't look too out of place to a Python programmer. C
functions have a return type first, the name, and then the typed
arguments inside the parenthesis. Lastly, the body of the function
resides between the curly braces. The function name `main` is how
the run-time linker (the program that runs programs) decides where
to start executing your program. If you write a C program and don't
include a function named `main`, it will not do anything. Harsh but
fair.

The function argument variables `argc` and `argv` together describe a
list of strings which were typed on the command line when the program
was invoked. In typical terse UNIX naming tradition, `argc` means
_argument count_ and `argv` means _argument vector_. Vector sounds
cooler than list and `argl` would have sounded like a strangled cry
from help.

## Moving On

```console
$ ./myprog foo bar -x baz
```

If `myprog` where implemented in C, `argc` would have the value 4 (C
is a zero indexed language, like Python), and `argv` would be an
array of pointers to characters with five entries (don't worry if that
sounds super-technical, it's a list of five strings). The first entry,
`argv[0]`, will be the name of the program. The rest of `argv` will
be the the arguments:
```C
   argv[1] == "foo"
   argv[2] == "bar"
   argv[3] == "-x"
   argv[4] == "-baz"
   
   /* Note: not valid C */
```	

In C, we have many choices to handle the strings in `argv`. We could
loop over the array `argv` _manually_ and interpret each of the
strings according to the needs of the program. This is relatively
easy, but leads to command lines with wildly different interfaces as
different programmers have different ideas about what is "good".

The next weapon in the command-line arsenal is a [C standard library][14]
function called [`getopt`][15]. This function allows the programmer to
parse switches, arguments with a dash preceeding it like '-x' and
optionally pair follow-on arguments with their switches. Think
about commands like `ls -alSh`, `getopt` is the function originally
used to parse that argument string. Using `getopt` makes parsing
the command-line pretty easy and improves the user experience. 

The [GNU][1] project came along and introduced longer format
command-line arguments for their implementations of traditional UNIX
command-line tools, things like '--file-format foo'. Of course we real
UNIX programmers hated that, but like the dinosaurs we are, we lost.
These arguments also tended to have short names like '-f foo' that had
to be interpreted too.  All of this choice resulted in more workload
for the programmer who just wanted to know what the user was
requesting and get on with it.  But the user got an even more
consistent user experience (UX); long and short format options and
automatic generation of help that keept the user from reading your
terrible manual page (see [`getopt`][15]).

## But We're Talking About Python?

That's enough history for you to have some context about how command
line interfaces work with our favorite language. Python gives us a
similar number of choices for command line parsing; do it yourself, a
battries-included option and several third-party options.

In the DIY category, we can get our program's arguments from the [`sys`][16]
module. This program just prints the values of the list `sys.argv`.
It's named `argv` because C programmers wrote the first Python
implementation and we give up our names for no one! Again, `argl`
would just be weird.

```python
import sys

if __name__ == '__main__':
   for value in sys.argv:
       print(value)
```

You can see the C heritage in this short program. There's a reference
to `main` and `argv`. The name `argc` is missing since Python list
objects incorporate the concept of length (or count) internally. If
you are writing a quick throw-away script, this is probably your
go-to move. 

## Batteries Included

There have been several iterations of argument parsing modules in the
Python standard library; [`getopt`][3], [`optparse`][4], and most
recently [`argparse`][5]. `Argparse` allows the programmer to provide
the user with a pretty consistent and helpful UX, but like it's GNU
antecedents it took a lot of work and ['boiler plate code'][17] on the
part of the programmer to make it "good".

```python
from argparse import ArgumentParser

if __name__ == '__main__':

   argparser = ArgumentParser(description='My Cool Program')
   argparser.add_argument('--foo', '-f', help='A user supplied foo')
   # more argument definitions 
   
   results = argparser.parse_args()
   print(results.foo)
```
   
## A Modern Approach to CLIs

And then there was[Click][6]. The `Click` package uses a
[decorator][7] approach to building command-line parsing. The
advantage is a powerful argument parsing engine with a consistent
interface which allows the programmer to reduce code while really
improving the user experience. Any time you can write less code and
still get things done is a "win". And we all want "wins". Experienced
programmers prefer library solutions to "roll-your-own" solutions
since they tend to handle all the corner and edge cases that we
haven't considered in our own solution.

```python
import click

@click.command()
@click.option('-f', '--foo', default='foo', help='User supplied foo.')
@click.option('-b', '--bar', default='bar', help='User supplied bar.')
def echo(foo, bar):
	print(foo, bar)
	
if __name__ == '__main__':
    echo()
```

You can see some of the same boiler plate code in the `click.option`
decorator as you saw with `argparse`. But the "work" of creating and
managing the argument parser has been abstracted away. Now the function
`echo` is called _magically_ with the command-line arguments parsed.

Adding arguments to a `click` interface is as easy as adding another
decorator to the stack and adding the new argument to the function
definition. 

## But Wait, There's More!

Built on-top of `Click`, [`typer`][8] is an even newer CLI framework
which combines the functionality of `Click` with modern Python [type
hinting][10]. One of the drawbacks of using `Click` is the boiler plate
decorators that have to be added to a function. Arguments to a
function (and a CLI) had to be specified in two places; the decorator
and the function argument. `Typer` [DRYs][9] out CLI specifications,
resulting in code that's easier to read and maintain.

```python
import typer

typer = typer.Typer()

@typer.command()
def echo(foo: str = 'foo', bar: str = 'bar'):
	print(foo, bar)
	
if __name__ == '__main__':
    typer.run()
```

Which one of these approaches is right? It depends on your use
case. Is it a quick and dirty script? Just use `sys.argv` directly and
drive on. Do you need more robust command-line parsing? Maybe
`argparse` is enough. Maybe you have lots of subcommands and
complicated options? Now you should definitely consider `Click` or
`Typer`.  Personally, these days I prefer `Typer` but it's not without
it's own collection of warts and goinks.




[0]: https://opensource.com/article/19/5/how-write-good-c-main-function
[1]: link to GNU project
[2]: link to what is a UNIX manual page 
[3]: docs.python.org getopt
[4]: docs.python.org optparse
[5]: docs.python.org argparse
[6]: pallets click
[7]: docs.python.org decorators
[8]: typer
[9]: definiton for DRY Don't Repeat Yourself
[10]: description of python type hinting
[11]: unix family tree wikipedia page
[12]: c language wikipedia page
[13]: unix wikipedia page
[14]: c standard library wiki page
[15]: getopt man page
[16]: docs.python.org for sys module
[17]: definition of boiler plate code
