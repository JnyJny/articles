<!-- 
author: Erik O'Shaughnessy
date: 23 Apr 2020
-->

# An Exploration of Modern Python Command Line Interface Design

The goal here is simple: help the new Python developer with some of
the history and terminology around command line interfaces (CLIs)
and explore how we write these useful programs in Python.

## In the Beginning...

First, some history about command line design from a [Unix][11]
persepective.

Unix is a computer operating system and is the ancestor of Linux and
MacOS (and [many other operating systems][11] as well). The primary
language for developing programs under Unix is [C][12], which has
amazing power and expressiveness.  C is the language that built the
Internet and most of the cool things that we rely on everyday: web
browsers, web servers, operating systems, DNS, TCP/IP, and nearly
every other piece of software that contributes to the ecosystem of
today's Internet.

So it behooves us to at least understand the basics of a [C program][0] .

Assuming you didn't read that, the basic architecture of a C program
is a function called **`main`** whose signature looks like:

```C
   int main(int argc, char **argv)
   {
   ...
   }
```

This shouldn't look too strange to a Python programmer. C functions
have a return type first, the name, and then the typed arguments
inside the parenthesis. Lastly, the body of the function resides
between the curly braces. The function name **`main`** is how the
run-time linker (the program that runs programs) decides where to
start executing your program. If you write a C program and don't
include a function named **`main`**, it will not do anything. Harsh but
fair.

The function argument variables `argc` and `argv` together describe a
list of strings which were typed on the command line when the program
was invoked. In typical terse Unix naming tradition, `argc` means
_argument count_ and `argv` means _argument vector_. Vector sounds
cooler than list and `argl` would have sounded like a strangled cry
from help.

## Moving On

```console
$ ./myprog foo bar -x baz
```

If `myprog` is implemented in C, `argc` will have the value 4 (C is a
zero indexed language, like Python), and `argv` will be an array of
pointers to characters with five entries (don't worry if that sounds
super-technical, it's a list of five strings). The first entry in the
vector, `argv[0]`, will be the name of the program. The rest of `argv`
will contain the arguments:

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
easy, but leads to programs with wildly different interfaces as
different programmers have different ideas about what is "good".

The next weapon in the command line arsenal is a [C standard
library][14] function called [`getopt`][15]. This function allows the
programmer to parse switches, arguments with a dash preceeding it like
'-x' and optionally pair follow-on arguments with their
switches. Think about command invocations like `/bin/ls -alSh`,
`getopt` is the function originally used to parse that argument
string. Using `getopt` makes parsing the command line pretty easy and
improves the user experience.

The [GNU][1] project came along and introduced longer format arguments
for their implementations of traditional Unix command line tools,
things like `--file-format foo`. Of course we _real_ Unix programmers
hated that because it was too much to type, but like the dinosaurs we
are, we lost because the users _liked_ them.

GNU-style arguments also tended to have short names like '-f foo' that
had to be interpreted too.  All of this choice resulted in more
workload for the programmer who just wanted to know what the user was
requesting and get on with it.  But the user got an even more
consistent user experience (UX); long and short format options and
automatically generated help that kept the user from having to read a
difficult manual page (see [`getopt`][15]).

## But We're Talking About Python?

That should be enough commmmand-line history for you to have some
context about how command line interfaces work with our favorite
language. Python gives us a similar number of choices for command line
parsing; do it yourself, a battries-included option and several
third-party options.

### Do It Yourself

We can get our program's arguments from the [`sys`][16] module. This
program just prints the values of the list `sys.argv`.  It's named
`argv` because a C programmer wrote the first Python implementation
and he probably didn't want to come up with a new name. Again, `argl`
would just be weird. Preserving those names across languages also
makes Python seem more friendly to C programmers. The downside is
new Python programmers are like "whuuuut?".

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

### Batteries Included

There have been several implementations of argument parsing modules in
the Python standard library; [`getopt`][3], [`optparse`][4], and most
recently [`argparse`][5]. `Argparse` allows the programmer to provide
the user with a pretty consistent and helpful UX, but like it's GNU
antecedents it took a lot of work and ['boilerplate code'][17] on the
part of the programmer to make it "good".

```python
from argparse import ArgumentParser

if __name__ == '__main__':

   argparser = ArgumentParser(description='My Cool Program')
   argparser.add_argument('--foo', '-f', help='A user supplied foo')
   argparser.add_argument('--bar', '-b', help='A user supplied bar')
   # more argument definitions 
   
   results = argparser.parse_args()
   print(results.foo, results.bar)
```

The payoff for the user is the automatically generated help available
when the user invokes the program with `--help`.

   
### A Modern Approach to CLIs

And then there was [Click][6]. The `Click` framework uses a
[decorator][7] approach to building command line parsing. The primary
advantage is it's powerful argument parsing engine with a consistent
interface which allows the programmer to reduce code while really
improving the user experience. Any time you can write less code and
still get things done is a "win". And we all want "wins". Experienced
programmers generally prefer library solutions to homegrown solutions
since libraries tend to handle all the corner and edge cases that we
haven't considered in our own solution. [Not invented here][18] is
real.

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

You can see some of the same boilerplate code in the `click.option`
decorator as you saw with `argparse`. But the "work" of creating and
managing the argument parser has been abstracted away. Now the function
`echo` is called _magically_ with the command line arguments parsed.

Adding arguments to a `click` interface is as easy as adding another
decorator to the stack and adding the new argument to the function
definition. 

## But Wait, There's More!

Built on top of `Click`, [`typer`][8] is an even _newer_ CLI framework
which combines the functionality of `Click` with modern Python [type
hinting][10]. One of the drawbacks of using `Click` is the stack of
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
case. Are you writting a quick and dirty script? Just use `sys.argv`
directly and drive on. Do you need more robust command line parsing?
Maybe `argparse` is enough. Maybe you have lots of subcommands and
complicated options? Now you should definitely consider `Click` or
`Typer`.  Personally, I prefer `Typer` but it's not without it's own
collection of warts and goinks.

Finally, there are _many_ third-party packages for parsing
command line arguments in Python. I've only presented the ones I like
or have used. It is entirely fine and expected for you to like and use
different packages. My advice is to start with these and see where you
end up.

## 

<!-- URLS -->
[0]: https://opensource.com/article/19/5/how-write-good-c-main-function
[1]: https://www.gnu.org
[2]: https://en.wikipedia.org/wiki/Man_page
[3]: https://docs.python.org/2/library/getopt.html
[4]: https://docs.python.org/2/library/optparse.html
[5]: https://docs.python.org/3/library/argparse.html
[6]: https://click.palletsprojects.com/en/7.x/
[7]: https://wiki.python.org/moin/PythonDecorators
[8]: https://typer.tiangolo.com
[9]: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself
[10]: https://docs.python.org/3/library/typing.html
[11]: https://en.wikipedia.org/wiki/Unix
[12]: https://en.wikipedia.org/wiki/C_(programming_language)
[14]: https://en.wikipedia.org/wiki/C_standard_library
[15]: http://man7.org/linux/man-pages/man3/getopt.3.html
[16]: https://docs.python.org/3/library/sys.html
[17]: https://en.wikipedia.org/wiki/Boilerplate_code
