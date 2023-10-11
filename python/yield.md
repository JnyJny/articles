# What The Heck Is Yield For?

A question came up recently about the purpose of the Python `yield`
expression and when you should use it.

Consider this silly function that computes a list of integers from 0
to 99 raised to the given exponent:

```python
def powers(exponent: int) -> list[int]:
    return [n**exponent for n in range(0, 100)]

>>> powers(2)
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256, 289, 324, 361, 400, 441, 484, 529, 576, 625, 676, 729, 784, 841, 900, 961, 1024, 1089, 1156, 1225, 1296, 1369, 1444, 1521, 1600, 1681, 1764, 1849, 1936, 2025, 2116, 2209, 2304, 2401, 2500, 2601, 2704, 2809, 2916, 3025, 3136, 3249, 3364, 3481, 3600, 3721, 3844, 3969, 4096, 4225, 4356, 4489, 4624, 4761, 4900, 5041, 5184, 5329, 5476, 5625, 5776, 5929, 6084, 6241, 6400, 6561, 6724, 6889, 7056, 7225, 7396, 7569, 7744, 7921, 8100, 8281, 8464, 8649, 8836, 9025, 9216, 9409, 9604, 9801]
>>> sum(powers(2))
328350
```

When called, this function runs thru all 100 integers in the range
computing each term and then returns the list to the caller. We can
sum the list and get the expected result.

This function will return to the caller pretty quickly, however when
the number of items being processed grows much larger, say two
billion, then the delay between calling the function and getting back
the result can be substantial. In addition to time, there is also a
space consideration. One hundred items in a list is not a lot of
memory:

```python
>>> import sys
>>> sys.getsizeof(list(range(0, 100)))
856
```

This snippet tells us that a list of 100 integers is 856 bytes in
memory. A 64-bit integer is 8 bytes so there is just a little bit of
overhead, 56 bytes, associated with the list. Not too bad. But small
programs rarely stay small. This little bit of code brought my laptop
to its knees and took upwards of 60 seconds to complete:

```python
>>> sys.getsizeof(list(range(0, 2_000_000_000)))
16000000056
```

I generated a list of two billion integers and asked for its size. As
expected, the two billion 64-bit integers takes up 16 billion bytes
and there is a 56 byte overhead for the list. So not only did it take
a long time to generate that list, that list is taking up a big chunk
of memory real estate.

So where does yield come in to play here?  Python treats functions
with yield expressions differently than it does regular functions.
Lets look at this generator function that performs the same operation
as the `powers` function:

```python
from typing import Generator

def powers_generator(exponent: int) -> Generator[int, None, None]:
    for n in range(0, 100):
        yield n**exponent
		
>>> powers_generator(2)
<generator object powers_generator at 0x10496e960>
>>> sum(powers_generator(2))
328350
```

This function is called the same way, however the return value type
hinting is a little more complex.  The `Generator` type hint has three
hint arguments; the `yield` type hint, the `send` type hint and the
`return` type hint. Starting with the return type hint, notice that
`powers_generator` does not have a return expression and that agrees
with the return type hint of `None`. I’m going to gloss over send and
its uses right now, so it is also type hinted with None. That leaves
the yield type hint, `int`, which agrees with the code in the body of
the function.

When the `powers_generator` function is called, it begins iterating thru
the range of 0 to 100 and the yield expression immediately returns the
computed value to the caller. This has two benefits; the caller gets
the computed value quicker and there isn’t any additional memory
consumed to hold all the computed values.

Notice that generator functions are used a little differently than
other iterators. When we called the function it returned something
weird:

```python
>>> powers_generator(2)
<generator object powers_generator at 0x10496ec00>
```

It returned a generator object which is a kind of __Iterable__ (it has
`__iter__` and `__next__` magic methods).  Each time the generator’s
`__next__` method is called, the function picks up just after the yield
and starts executing until it yields again, raises an exception or
returns.

What’s cool about that is the context of the function is available to
it when it begins executing again. In the case of our toy function, it
knows where it's at in the range of 0 to 99 and therefore the next
value to compute.

Another difference between a generator function and an __Iterable__
like a list or a dictionary is generators are “single use”. If you
have a list, you can iterate over it multiple times. However after a
generator function returns it is _exhausted_. Calling it again results
in no values returned. For instance, in this next code example we
create a list of powers of two and a generator. The list can be summed
multiple times and produces the expected value, while summing the
generator function works as expected the first time and results in
zeros when summed again.

```python
>>> l = powers(2)
>>> sum(l)
328350
>>> sum(l)
328350

>>> g = powers_generator(2)
>>> sum(g)
328350
>>> sum(g)
0
```

Ok, yield expressions make generators and generators can reduce
latency by returning values to the caller sooner and can reduce memory
use by generating its values on the fly. But what do “real” programs
use it for?  One neat use is in creating context managers using the
`contextlib.contextmanager` decorator:

```python
from contextlib import contextmanager

@contextmanager
def manager():
    print("setup")
    yield
    print("teardown")

>>> with manager():
...     print("inside")
... 
setup
inside
teardown
```

Python context manager expressions begin with the `with` keyword and
can help manage a resource like an open file or a database
connection. In this simple bit of code, we have some sophisticated
behavior!  Here we are simply printing out the different phases of a
context manager; setup, inside and teardown. The `yield` in the
`manager` function gives the nested code in the body of the `with`
statement the opportunity to run. When the code block finishes,
control is handed back to the manager function just after the yield.

The pytest package uses this pattern extensively to allow the user to
create testing fixtures of arbitrary complexity.

Just remember, if you see `yield` in a function then it’s a
generator. Generators are one-time use only but can reduce latency and
conserve memory.
