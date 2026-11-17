<!--
Author: Erik O'Shaughnessy
Editor: Claude
Date: November 2026
Status: draft
Series: C Programming
Prerequisites: pointers, integers
Next: none
-->

# Sizing Things Up: sizeof

`sizeof` is on nearly every page of C code, and it is often misread. It
looks like a function and isn't one. It returns a number that misbehaves
in ways that are easy to miss. It gives the wrong answer for an array in
just the place you most want the right one. In this article we're going
to look at what `sizeof` is, what it returns and where it lets you down.

**Me**: a crusty Unix system programmer who uses `sizeof` all the time
and has opinions about it.

**You**: someone who has written some C and has typed `sizeof` without
being completely sure what it is.

Let's measure some things.

## An Operator

`sizeof` looks like a function call, and it isn't one. A function runs
while the program runs, receives the values you pass it and can't be
handed a type. `sizeof` is an _operator_, like `+` or `*`, a piece of
the language that the compiler works out for itself. A short program
shows what that means:

```C
/* operator.c - sizeof looks like a function call and isn't one */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int counter = 5;
    size_t first = sizeof(counter++);
    size_t second = sizeof counter;
    size_t third = sizeof(long);

    printf("counter = %d\n", counter);
    printf("%zu %zu %zu\n", first, second, third);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o operator operator.c
$ ./operator
counter = 5
4 4 8
```

Three things happened. First, `sizeof(counter++)` never ran its operand,
so `counter` is still 5. The compiler only needed the type of the
expression to know its size, and a function would have run the
increment. Second, `sizeof counter` works without parentheses, because
an expression doesn't need them. Third, `sizeof(long)` took a type. A
type does need the parentheses, and `sizeof long` is a compile error. A
function can't take a type at all.

## What It Returns

The `sizeof` operator gives you the size of a type or a variable, in
bytes, as a `size_t`. That's an unsigned integer, so `sizeof` inherits
every trap that unsigned integers have, and [the integers
article][integers] has plenty to say about those. Here are two of them,
and an idiom:

```C
/* sizeof.c - sizeof is an unsigned number of bytes */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int values[10];
    int count = -1;
    size_t difference = sizeof(int) - 5;

    if (count < sizeof(int))
        printf("-1 < sizeof(int)\n");
    else
        printf("-1 >= sizeof(int)\n");
    printf("sizeof(int) - 5 = %zu  0x%016zx\n", difference, difference);
    printf("bytes    = %zu\n", sizeof(values));
    printf("elements = %zu\n", sizeof(values) / sizeof(*values));
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -Wsign-compare -o sizeof sizeof.c
sizeof.c: In function 'main':
sizeof.c:11:15: warning: comparison of integer expressions of different signedness: 'int' and 'long unsigned int' [-Wsign-compare]
   11 |     if (count < sizeof(int))
      |               ^
$ ./sizeof
-1 >= sizeof(int)
sizeof(int) - 5 = 18446744073709551615  0xffffffffffffffff
bytes    = 40
elements = 10
```

The comparison is false. The -1 was converted to unsigned, the same
thing that made `-1 < 1u` false in [the integers
article][integers-compare]. The subtraction wrapped around like the
`strlen(a) - strlen(b)` example in [counting down with
`size_t`][integers-countdown]. When you compare a count with a `sizeof`,
make the count a `size_t`, and read the warning when the compiler offers
one.

The last two lines are an idiom you will see all over C code.
`sizeof(values)` is the size of the whole array in bytes: ten `int`s of
4 bytes each is 40. Divide by the size of one element and you have the
number of elements. I divide by `sizeof(*values)`, the size of whatever
`values` holds, so that the line stays right when somebody changes the
array to `long`. Divide by `sizeof(int)` and the line is wrong the
moment the type changes.

## When the Array Turns Into a Pointer

The idiom has a limit. It works where the compiler still knows that
`values` is an array, which is in the function that declared it. Pass
the array to another function and look again:

```C
/* parameter.c - an array that is passed along turns into a pointer */
#include <stdio.h>
#include <stdlib.h>

void inner(int values[10]);

int main(int argc, char *argv[])
{
    int values[10];

    printf("in main:  %zu\n", sizeof(values));
    inner(values);
    return EXIT_SUCCESS;
}

void inner(int values[10])
{
    printf("in inner: %zu\n", sizeof(values));
}
```

```console
$ gcc -Wall -o parameter parameter.c
parameter.c: In function 'inner':
parameter.c:18:37: warning: 'sizeof' on array function parameter 'values' will return size of 'int *' [-Wsizeof-array-argument]
   18 |     printf("in inner: %zu\n", sizeof(values));
      |                                     ^
parameter.c:16:16: note: declared here
   16 | void inner(int values[10])
      |            ~~~~^~~~~~~~~~
$ ./parameter
in main:  40
in inner: 8
```

Inside `inner()`, `values` is an `int *`, and `sizeof` reports the size
of a pointer, which is 8 bytes on this machine. The `[10]` in the
parameter is a comment the compiler ignores. gcc warns about it, and gcc
is right. The pointers article explains how [arrays decay to
pointers][pointers-arrays], and [the ways C spells an array][arrays] has
the rest. When a function needs to know how many elements an array has,
pass the count as another argument.

## Macros

A macro is a third kind of thing. The [preprocessor][cpp] replaces macro
text before the compiler sees any C, and it knows nothing about types.
That's why `sizeof` can't be a macro, and why the preprocessor can't use
it. Ask it a question in an `#if` and you get an error:

```console
$ cat iftest.c
#if sizeof(int) == 4
int four = 1;
#endif
$ gcc -c iftest.c
iftest.c:1:11: error: missing binary operator before token "("
    1 | #if sizeof(int) == 4
      |           ^
```

What a macro can do is give a name to an idiom. You will often see the
element-count line wrapped up like this: `#define COUNT(a) (sizeof(a) /
sizeof(*(a)))`. The macro expands to the same text, so it has the same
blind spot. Hand it a pointer and, on this machine, it divides 8 by 4
and says 2. gcc catches that one with `-Wsizeof-pointer-div`, which
`-Wall` turns on.

## Where To Go From Here

Try `sizeof` on things you have written: a structure, a pointer and a
string literal, and predict each answer before you run it. Padding can
make a structure larger than the sum of its members, so that answer may
surprise you. The story of why belongs with [what a type
is][data-types]. Then look for the element-count idiom in code you
maintain, and check that every use is looking at an array and not at a
pointer that used to be one.

<!-- Links -->
[integers]: ../integers/article.md
[integers-compare]: ../integers/article.md#when-signed-meets-unsigned
[integers-countdown]: ../integers/article.md#counting-down-with-size_t
[pointers-arrays]: ../pointers/article.md#pointers-and-arrays
[arrays]: ../arrays/article.md
[cpp]: ../compiler-tool-chain/article.md#cpp
[data-types]: ../data-types/article.md
