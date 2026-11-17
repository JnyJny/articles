<!--
Author: Erik O'Shaughnessy
Editor: Claude
Date: November 2026
Status: draft
Series: C Programming
Prerequisites: memory-allocation
Next: none
-->

# Do Not Fold, Spindle, or Mutilate: C Integers

Punch cards used to carry a warning: do not fold, spindle or mutilate.
The card was the data, and a damaged card meant a wrong answer, handed
back with total confidence. Integers in C are like that. The `int` looks
like the safest thing in the language, since you learned to count with
it, and it comes with a whole set of ways to get the wrong answer
without a word of complaint from the compiler. In this article we're
going to fold, spindle and mutilate some integers on purpose, so that
you can recognize the damage when it shows up in your own programs.

**Me**: a crusty Unix system programmer who has been surprised by
arithmetic more often than I'd like.

**You**: someone who has written some C, trusts `+` and `<`, and wants
to know when to stop.

Every program here was compiled with gcc 14 and run on aarch64 Linux.
Where x86-64 gives a different answer, I ran it there too and I say so.
Your machine may disagree with both of us, and that's half the point.

Let's start breaking things.

## Bits Don't Know What They Mean

Eight bits make a byte, and a byte has 256 possible patterns. Which
numbers those patterns stand for is up to the type of the variable that
holds them. A word on notation before we go on: I write binary with a
`0b` prefix and hex with `0x`, the way C does, and a number with no
prefix is decimal. As an unsigned integer, the patterns `0b00000000`
through `0b11111111` mean 0 through 255. As a signed integer, nearly
every machine you will meet uses [two's complement][twos-complement],
where the top bit counts as -128 instead of +128. This program prints
each pattern in binary and in hex, followed by the signed and unsigned
readings:

```C
/* bits.c - the same bits, written and read several ways */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void show(int8_t value);

int main(int argc, char *argv[])
{
    int8_t values[] = {0, 1, 2, 126, 127, -128, -127, -2, -1};

    for (size_t i = 0; i < sizeof(values) / sizeof(*values); i++)
        show(values[i]);
    return EXIT_SUCCESS;
}

void show(int8_t value)
{
    uint8_t bits = (uint8_t)value;

    fputs("0b", stdout);
    for (int i = 7; i >= 0; i--)
        fputc((bits >> i) & 1 ? '1' : '0', stdout);
    printf("  0x%02x  %4d  %3u\n", bits, value, bits);
}
```

```console
$ gcc -Wall -o bits bits.c
$ ./bits
0b00000000  0x00     0    0
0b00000001  0x01     1    1
0b00000010  0x02     2    2
0b01111110  0x7e   126  126
0b01111111  0x7f   127  127
0b10000000  0x80  -128  128
0b10000001  0x81  -127  129
0b11111110  0xfe    -2  254
0b11111111  0xff    -1  255
```

Read the last row. `0b11111111` is 255 as an unsigned integer and -1 as
a signed one. The bits are identical. Nothing in memory records which
reading is right. The type on the variable decides, and the compiler
picks machine instructions to match.

The hex column is there to build your intuition for it. Hex is binary
written more compactly: each hex digit stands for four bits, so a byte
is always two digits. `0b0111` is `7`, `0b1000` is `8` and `0b1111` is
`f`, which makes `0b01111111` into `0x7f`, `0b10000000` into `0x80` and
`0b11111111` into `0xff`. Those three turn up everywhere, and they're
worth recognizing on sight.

Two facts from that table will matter for the rest of this article.
First, -1 is all ones, in every width. Second, look at the jump from
`0b01111111` to `0b10000000`, where 127 turns into -128 with one more
step. The negative side has one more value than the positive side, so
there is no +128 to be the mirror image of -128. We'll fall off that
cliff more than once.

To negate a number in two's complement, flip every bit and add one. Try
it on 1: flip `0b00000001` to `0b11111110`, add one, and you get
`0b11111111`, which is -1. The reason machines work this way is that the
adder doesn't need to know about signs. Add one to `0b11111111` and the
carry falls off the end, leaving `0b00000000`, which is the right answer
for both readings. One circuit serves signed and unsigned arithmetic,
and the side effects of that economy are the subject of the rest of
this article.

## How Big Is an int?

Less than you might hope for. The C standard promises minimums: `char`
is at least 8 bits, `short` and `int` at least 16, `long` at least 32,
and `long long` at least 64. What your compiler picks above that is its
business. Ask it:

```C
/* sizes.c - how big are the integer types here? */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    printf("char      %zu\n", sizeof(char));
    printf("short     %zu\n", sizeof(short));
    printf("int       %zu\n", sizeof(int));
    printf("long      %zu\n", sizeof(long));
    printf("long long %zu\n", sizeof(long long));
    printf("size_t    %zu\n", sizeof(size_t));
    printf("CHAR_MIN  %d\n", CHAR_MIN);
    printf("INT_MIN   %d\n", INT_MIN);
    printf("INT_MAX   %d\n", INT_MAX);
    printf("UINT_MAX  %u\n", UINT_MAX);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o sizes sizes.c
$ ./sizes
char      1
short     2
int       4
long      8
long long 8
size_t    8
CHAR_MIN  0
INT_MIN   -2147483648
INT_MAX   2147483647
UINT_MAX  4294967295
```

The `%zu` format is the one for a `sizeof` result, which has the type
`size_t`. On this machine an `int` has 4 bytes and a `long` has 8. When
the width matters, such as in a file format, a network packet or a
hardware register, stop asking the compiler what `int` means and say
what you mean with the types in `<stdint.h>`: `uint8_t`, `int32_t`,
`uint64_t` and friends. Their names carry their widths. Use plain `int`
for a small counter that will never be small enough to worry about, and
`size_t` for sizes and counts of things in memory.

Now look at the `CHAR_MIN` line. On this machine, plain `char` is
unsigned. We'll come back to that.

## The Odometer

An unsigned integer that runs off the top comes back around to zero,
like a car odometer rolling over from 99999 to 00000. The standard
defines this: unsigned arithmetic is done modulo 2 to the power of the
width. That is a feature. Hash functions, ring buffers and sequence
numbers depend on it.

```C
/* wrap.c - unsigned integers roll over */
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    unsigned int u = UINT_MAX;
    unsigned char c = 255;
    uint32_t count = 1U << 30;
    uint32_t bytes = count * (uint32_t)sizeof(int);

    printf("u + 1  = %u\n", u + 1);
    c++;
    printf("c++    = %u\n", c);
    printf("0u - 1 = %u\n", 0U - 1);
    printf("bytes  = %u\n", bytes);
    printf("wide   = %zu\n", (size_t)count * sizeof(int));
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o wrap wrap.c
$ ./wrap
u + 1  = 0
c++    = 0
0u - 1 = 4294967295
bytes  = 0
wide   = 4294967296
```

The first three lines are the odometer at work. Going one below zero
lands on the biggest number the type can hold, which is how an innocent
`0u - 1` becomes 4294967295.

The last two lines are the one that bites. A billion `int`s need 4
billion bytes, which doesn't fit in 32 bits, so the 32-bit product
wraps to zero. Hand that size to `malloc()` and you get a valid pointer
to a block far too small, and then a loop that writes a billion integers
into it. That's the trap that `calloc()` caught in [borrowing
memory][memory-allocation]. The arithmetic there was done in 64 bits,
and the numbers were bigger, but the mechanism is the same.

## Signed Overflow Is Undefined

Signed integers look like they should wrap the same way. On this machine
`INT_MAX + 1` does print -2147483648, which is what two's complement
predicts. The standard, however, doesn't promise it. When signed
arithmetic overflows, the behavior is _undefined_, which means the
compiler is allowed to assume it never happens, and then to generate
code that is only right for programs where it doesn't.

Here's a test that looks reasonable. If `x + 1` is less than `x`, then
adding one wrapped around:

```C
/* ub.c - a test that can't be true */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

int will_wrap(int x);

int main(int argc, char *argv[])
{
    int x = INT_MAX;

    printf("will_wrap(%d) = %d\n", x, will_wrap(x));
    return EXIT_SUCCESS;
}

int will_wrap(int x)
{
    return x + 1 < x;
}
```

```console
$ gcc -Wall -o ub ub.c
$ ./ub
will_wrap(2147483647) = 0
```

Zero. The function says that `INT_MAX + 1` does not wrap around, which
is wrong. The compiler reasoned that for any `int`, `x + 1` can't be
smaller than `x` unless overflow happened, overflow can't happen, so the
test is always false and doesn't need to be computed. I got the same
answer with `-O2`. Neither run printed a warning.

You have three ways to catch this, and I use all of them. The first is
to ask the compiler to check at run time:

```console
$ gcc -Wall -fsanitize=undefined -o ub ub.c
$ ./ub
ub.c:18:14: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
will_wrap(2147483647) = 1
```

The `-fsanitize=undefined` flag is documented with the rest of
[gcc's instrumentation options][gcc-instrumentation]. It's slower, so it
belongs in testing. The second is `-ftrapv`, which makes signed overflow
abort the program. The third is to write the test so that it can't
overflow in the first place:

```C
int will_wrap(int x)
{
    return x == INT_MAX;
}
```

Check against the limit before the arithmetic, not after. There is also
`-fwrapv`, which tells gcc to define signed overflow as wrapping. It
makes this program print 1, and I'd use it only to buy time while
fixing the code, because it changes the language for every file you
compile with it, whether or not that file's author knew.

## When Signed Meets Unsigned

Mix a signed and an unsigned integer in one expression and C has to pick
a type for the arithmetic. The rule has a few steps, and the result is
the sort of thing that makes people distrust the language. Anything
narrower than an `int` is first promoted to `int`. Then, if an `int`
meets an `unsigned int`, the `int` is converted to unsigned.

```C
/* compare.c - signed meets unsigned */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int a = -1;
    unsigned int b = 1;
    unsigned char x = 200;
    unsigned char y = 100;
    unsigned char z = x + y;
    char c = 200;

    if (a < b)
        printf("-1 < 1u\n");
    else
        printf("-1 >= 1u\n");
    printf("x + y = %d\n", x + y);
    printf("z     = %u\n", z);
    printf("c     = %d\n", c);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -Wsign-compare -o compare compare.c
compare.c: In function 'main':
compare.c:14:11: warning: comparison of integer expressions of different signedness: 'int' and 'unsigned int' [-Wsign-compare]
   14 |     if (a < b)
      |           ^
$ ./compare
-1 >= 1u
x + y = 300
z     = 44
c     = 200
```

Minus one is not less than one. The `int` -1 was converted to unsigned,
where its all-ones pattern is 4294967295, and that is a long way from 1.
Fortunately gcc knows about this one and says so, if you ask:
`-Wsign-compare` is one of the warnings that `-Wextra` turns on. Read
the warnings on the first compile, because the next time you meet this
bug it will be in a loop condition in somebody else's code.

The promotion shows in the next two lines. The sum of two `unsigned
char`s is computed as an `int`, so `x + y` is 300, but storing it back
into an `unsigned char` keeps only the low 8 bits, and 300 becomes 44.

The last line is the `char` we left hanging. Plain `char` can be signed
or unsigned, and the standard leaves the choice to the compiler. On this
machine it is unsigned, so `c` holds 200. On x86-64 the same program
prints `c     = -56`, because there `char` is signed and 200 wraps to
-56. If you keep numbers in a variable, say `signed char` or `unsigned
char` (or `int8_t` or `uint8_t`), and leave plain `char` for text.

## Counting Down With size_t

A `size_t` is unsigned, and a loop that counts down to zero with it is
a classic. Here it is, with an escape hatch added so that it stops:

```C
/* countdown.c - an unsigned counter is never below zero */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    size_t n = 3;

    for (size_t i = n - 1; i >= 0; i--) {
        printf("%zu\n", i);
        if (i > 5) {
            printf("...and it never stops\n");
            break;
        }
    }
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -Wtype-limits -o countdown countdown.c
countdown.c: In function 'main':
countdown.c:9:30: warning: comparison of unsigned expression in '>= 0' is always true [-Wtype-limits]
    9 |     for (size_t i = n - 1; i >= 0; i--) {
      |                              ^~
$ ./countdown
2
1
0
18446744073709551615
...and it never stops
```

An unsigned number is always at least zero, so `i >= 0` can't fail. When
`i` reaches 0 and gets decremented, it rolls around to the largest
`size_t`, and the loop carries on into whatever memory `i` indexes. The
compiler warned again, this time with `-Wtype-limits`, which `-Wextra`
also turns on. This is the same bug as `strlen(a) - strlen(b)`
when `b` is the longer string: the subtraction can't go negative, so
it produces a huge positive number instead.

One fix is to test the old value and decrement afterward:

```C
for (size_t i = n; i-- > 0;)
    printf("%zu\n", i);
```

That prints 2, 1 and 0, and stops. Read `i-- > 0` as "while `i` is
greater than zero, and then take one off". It looks odd the first time.
It's worth memorizing anyway.

## Shifts

Shifting moves bits left or right. For an unsigned integer, shifting
left by one multiplies by 2, and shifting right by one divides by 2,
dropping the remainder. It's the binary version of moving a decimal
point.

```C
/* shifts.c - moving bits, and the ways that go wrong */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int count = argc > 1 ? atoi(argv[1]) : 32;
    unsigned int one = 1;
    int negative = -16;

    printf("1u << %d = %u\n", count, one << count);
    printf("-16 >> 2 = %d\n", negative >> 2);
    printf("(unsigned)-16 >> 2 = %u\n", (unsigned int)negative >> 2);
    printf("1 << 31 = %d\n", 1 << 31);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o shifts shifts.c
$ ./shifts
1u << 32 = 1
-16 >> 2 = -4
(unsigned)-16 >> 2 = 1073741820
1 << 31 = -2147483648
```

Four lines, three lessons.

Shifting right a negative number copies the sign bit into the vacated
positions, so -16 >> 2 is -4. That is what gcc does, and it documents
that it does. The standard calls the result implementation-defined,
which means a compiler is required to pick something and write down what
it picked. Shift the same bits as an unsigned integer and zeros come in
from the left, which gives 1073741820.

Shifting 1 left by 31 puts a one in the sign bit of an `int`. The
standard calls that undefined, even though the answer it printed here
looks reasonable. Run it under `-fsanitize=undefined` and you get `left
shift of 1 by 31 places cannot be represented in type 'int'`. Write it
as `1U << 31` when you want the top bit.

The first line is the strangest. Shifting a 32-bit value left by 32
places should give 0, since every bit gets shoved off the end. It gave
1. Run `./shifts 33` and the first line prints 2. The CPU, on both
aarch64 and x86-64, only looks at the low five bits of the shift count,
so 32 acts like 0 and 33 acts like 1. That's the hardware's habit. The
standard says that shifting by the width of the type or more is
undefined, and a compiler that knows the count ahead of time is free to
give a different answer. Keep the count between 0 and one less than the
width.

## Division

Integer division in C throws the fraction away, and for negative numbers
the direction matters. C rounds toward zero, and the remainder takes the
sign of the dividend, so that `(a / b) * b + a % b` is always `a`.

```C
/* divide.c - rounding, and the value with no mirror image */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int divisor = argc > 1 ? atoi(argv[1]) : -1;
    int smallest = INT_MIN;

    printf("-7 / 2  = %d  -7 %% 2  = %d\n", -7 / 2, -7 % 2);
    printf(" 7 / -2 = %d   7 %% -2 = %d\n", 7 / -2, 7 % -2);
    printf("-1 %% 8  = %d\n", -1 % 8);
    printf("abs(INT_MIN) = %d\n", abs(smallest));
    printf("INT_MIN / %d = ", divisor);
    fflush(stdout); /* so the label survives a crash */
    printf("%d\n", smallest / divisor);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o divide divide.c
$ ./divide
-7 / 2  = -3  -7 % 2  = -1
 7 / -2 = -3   7 % -2 = 1
-1 % 8  = -1
abs(INT_MIN) = -2147483648
INT_MIN / -1 = -2147483648
```

If you came from Python, where `-7 // 2` is -4 and `-7 % 2` is 1, this
is a trap. Python rounds toward negative infinity, and C rounds toward
zero. The one that gets people is `-1 % 8`, which is -1 in C. Code that
uses `%` to wrap an index around a ring of 8 slots gets a negative index
the first time it counts backward.

The last two lines are the missing mirror image from the first section.
The negative side has one more value, so `abs(INT_MIN)` is `INT_MIN`,
still negative. Negation of `INT_MIN` does the same. Dividing `INT_MIN`
by -1 should give 2147483648, which doesn't fit in an `int`, and what
happens next depends on your CPU. This machine returns `INT_MIN` and
carries on without a word. Run `./divide 0` and it prints
`INT_MIN / 0 = 0`: the hardware here defines division by zero as zero.

On x86-64, both of those die. `INT_MIN / -1` and `INT_MIN / 0` kill the
program with SIGFPE, which is a [signal][unix-signals] with a misleading
name, since there is no floating point involved. Both cases are
undefined in C. The CPUs just answer differently. If the divisor comes
from outside your program, a file, a socket or a command line, check
for 0 and -1 before you divide.

## Ask The Compiler

Checking an operation before doing it works, but you have to get the
check right for each operation and each type. There is an easier way
for addition, subtraction and multiplication: ask the compiler to do the
arithmetic and tell you if it wrapped. gcc and clang have built-ins for
that, and this program puts them to work:

```C
/* checked.c - find out whether the arithmetic wrapped */
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int checked_add(int a, int b, int *sum);
int checked_mul(size_t count, size_t size, size_t *bytes);

int main(int argc, char *argv[])
{
    int sum = 0;
    size_t bytes = 0;

    if (checked_add(INT_MAX, 1, &sum))
        perror("checked_add");
    if (checked_mul(1000, sizeof(int), &bytes))
        perror("checked_mul");
    else
        printf("1000 ints need %zu bytes\n", bytes);
    if (checked_mul(SIZE_MAX / 2, sizeof(int), &bytes))
        perror("checked_mul");
    return EXIT_SUCCESS;
}

int checked_add(int a, int b, int *sum)
{
    if (!sum) {
        errno = EINVAL;
        return EXIT_FAILURE;
    }
    if (__builtin_add_overflow(a, b, sum)) {
        errno = ERANGE;
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}

int checked_mul(size_t count, size_t size, size_t *bytes)
{
    if (!bytes) {
        errno = EINVAL;
        return EXIT_FAILURE;
    }
    if (__builtin_mul_overflow(count, size, bytes)) {
        errno = ERANGE;
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o checked checked.c
$ ./checked
checked_add: Numerical result out of range
1000 ints need 4000 bytes
checked_mul: Numerical result out of range
```

Each built-in does the arithmetic in infinite precision, stores the
low bits of the result in the last argument, and returns nonzero if the
true answer didn't fit. That's the right tool for sizes that will be
handed to `malloc()`. The C23 standard added the same idea as
`<stdckdint.h>`. With `-std=c23`, gcc 14 provides `ckd_add()`,
`ckd_sub()` and `ckd_mul()`, which put the destination first:
`ckd_add(&sum, a, b)`. Use the built-ins until your compilers all have
the header.

## Where To Go From Here

Compile every program in this article with `-fsanitize=undefined` and
see what the sanitizer has to say that the compiler didn't. Then run
`shifts` and `divide` on a second kind of machine, if you can borrow
one, a Raspberry Pi, a cloud server or your friend's laptop, and see
which of my results survive the trip. Write `checked_sub()` and give it
a test that fails when it should.

Then go looking for the bug in a program you already wrote. The most
likely hiding place is a `for` loop with an unsigned counter, a size
multiplied by a count, or a comparison between an `int` and a `size_t`.
When you're ready for the larger question of why every piece of data
needs a type to begin with, [that story is waiting][data-types].

<!-- Links -->
[twos-complement]: https://en.wikipedia.org/wiki/Two%27s_complement
[memory-allocation]: ../memory-allocation/article.md
[gcc-instrumentation]: https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html
[unix-signals]: ../../unix/signals/article.md
[data-types]: ../data-types/article.md
