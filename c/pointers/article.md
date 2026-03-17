# Pointers: Embrace the Dark Magic

Pointers are the thing in C that everybody's afraid of. This is
unfortunate, because pointers are also the thing in C that makes
everything else work. If you've been avoiding them, it's time to
stop. Pointers might seem scary but I think you'll find they aren't
too bad once you make friends.


**Me**: a crusty Unix system programmer who has dereferenced more
pointers than you've had hot dinners.

**You**: someone who knows a little C, has a compiler, and has heard
the word "pointer" spoken in hushed, fearful tones.

Let's fix that.

## Every Variable Lives Somewhere

Your computer has memory. It's where programs keep stuff. In fact all
their stuff. When you declare a variable, the compiler (with help from
the [linker][linker-aliens]) picks a spot in memory to put it. The
variable has a _value_ (the thing you put in it) and an _address_
(where it ended up).

```C
int x = 42;
```

What does this say? That `x` is a variable that can hold a signed
integer and we've assigned the value 42 to it. What you might not
think about is that `x` also has an address -- some number like
`0x4004` that identifies the specific address of the bytes in memory
where that 42 is being stored.

```
    Variable    Address    Value
    ┌────────┬──────────┬────────┐
    │ int x  │  0x4004  │     42 │
    └────────┴──────────┴────────┘
```

You don't normally care about addresses. You just say `x` and
the compiler figures out where to find it.

A pointer is a variable that holds an address instead of a regular
value. That's it. That's the whole thing.

## Declaring Pointers

A pointer declaration looks like a regular variable declaration with
an asterisk jammed in there:

```C
int *p = (int *)NULL;
```

This says: `p` is a pointer to an int. It doesn't _point_ to anything
useful yet -- we've explicitly set it to **NULL**, which means "points to
nothing on purpose." The cast `(int *)` matches the **NULL** to the
pointer's destination type. This is not strictly required, but it
makes the intent clear and I like it when types agree with each other.

What you absolutely do not want is an _uninitialized_ pointer -- one
where you never assigned it anything at all. An uninitialized pointer
contains whatever garbage was in that memory before. Using one is how
you get [spectacular crashes][segfault] and a reputation for writing
unreliable code.


Where you put the asterisk is a matter of personal style and the
center of a centuries-old religious conflict:

```C
int *p;     /* I do this  */
int* p;     /* some people do this */
int * p;    /* and some people do this */
```

They all mean the same thing to the compiler. I put the asterisk next
to the variable name because it makes multiple declarations less
surprising:

```C
int *p, *q;    /* two pointers to int, obviously */
int* p, q;     /* one pointer and one int, surprise! */
```

That second line declares `p` as a pointer to int and `q` as a plain
int. The asterisk binds to the variable name, not the type. This trips
up approximately 100% of new C programmers and a non-zero percentage
of experienced ones who should know better. Be like me and attach
that asterisk to the variable name.

## The Two Operators You Need

C gives you two operators for working with pointers. Just two. You can
learn two things.

### The Address-Of Operator: &

The `&` operator gives you the address of a variable:

```C
int x = 42;
int *p = &x;    /* p now holds the address of x */
```

After this, `p` contains the address where `x` lives in memory:

```
    Variable    Address    Value
    ┌────────┬──────────┬────────┐
    │ int x  │  0x4004  │     42 │◄─ ─ ┐
    └────────┴──────────┴────────┘     │  p's value IS
    ┌────────┬──────────┬────────┐     │  x's address
    │ int *p │  0x4000  │ 0x4004 │─ ─ ┘
    └────────┴──────────┴────────┘
```

We say "p _points to_ x" because that's less tedious than saying "p
contains the memory address at which the value of x is stored." Life
is short. Notice how the types of `x` and `*p` are both `int`. C will
let you mix and match types but it usually does not end well. 

### The Dereference Operator: *

The `*` operator follows a pointer to the thing it points at:

```C
int x = 42;
int *p = &x;

printf("%d\n", *p);    /* prints 42 */
```

When you write `*p`, you're saying "go to the address stored in p and
give me the value there." This is called _dereferencing_ and it's the
whole reason pointers exist.

Yes, the same `*` character is used both to declare a pointer and to
dereference one. No, this is not great language design. But C was
written in the early 1970s by people who were also inventing Unix at
the time, and they were busy. We forgive them because they gave us
everything else.

Here's where it gets interesting. Dereferencing isn't read-only:

```C
*p = 99;
printf("%d\n", x);    /* prints 99 */
```

We changed `x` without ever mentioning `x` by name. We went through
the pointer:

```
    Variable    Address    Value
    ┌────────┬──────────┬────────┐
    │ int x  │  0x4004  │ 42→99  │◄─ ─ ┐
    └────────┴──────────┴────────┘     │  *p = 99
    ┌────────┬──────────┬────────┐     │  writes through
    │ int *p │  0x4000  │ 0x4004 │─ ─ ┘   the pointer
    └────────┴──────────┴────────┘
```

This is not a parlor trick -- it's the fundamental mechanism that
makes C functions useful.

## Pointer Fun: Passing By Reference

Now, consider this toy function:

```C
void birthday(int age) {
    age = age + 1;
}

int main(int argc, char *argv[]) {
    int your_age = 20;
    birthday(your_age);
    printf("your_age: %d\n", your_age);    /* prints 20, not 21 */
    return EXIT_SUCCESS;
}
```

C passes arguments by value. When you call `birthday(your_age)`, the
function gets a _copy_ of the value 20. It happily increments its
local copy to 21, returns, and the copy evaporates. The original
variable is untouched. This is the number one source of confusion for
people coming from languages where everything is a reference.

Pointers fix this:

```C
void birthday(int *age) {
    *age = *age + 1;
}

int main(int argc, char *argv[]) {
    int your_age = 20;
    birthday(&your_age);
    printf("age: %d\n", your_age);    /* prints 21 */
    return EXIT_SUCCESS;
}
```

Now `birthday()` receives the _address_ of `your_age`. It
dereferences the pointer to read and write the original variable. The
copy that gets made is a copy of the _address_, not the value. Since
the address still points to the same variable, the function can modify
the caller's data.

If you've read [How I Write Main][how-i-write-main], you saw this
pattern in action:

```C
int do_the_needful(options_t *options);
```

This function takes a _pointer_ to an `options_t` structure, not a
copy of one. This means it can read and modify the caller's
structure, and it means we're not copying a whole structure onto the
[stack][names-and-spaces] every time we call the function. Two wins
for the price of one asterisk.

## Pointers and Arrays

Here's where C does something sneaky. Arrays and pointers are
intimately related -- close enough to be confusing, different enough
to be dangerous.

An array name, in most contexts, _decays_ to a pointer to its first
element:

```
    Variable    Address    Value
    ┌────────┬──────────┬────────┐
    │ int *p │  0x3000  │ 0x5000 │─ ─ ┐
    └────────┴──────────┴────────┘     │
                                       │
    ┌────────┬──────────┬────────┐     │
    │ int[0] │  0x5000  │     10 │◄─ ─ ┘
    ├────────┼──────────┼────────┤
    │ int[1] │  0x5004  │     20 │
    ├────────┼──────────┼────────┤
    │ int[2] │  0x5008  │     30 │
    ├────────┼──────────┼────────┤
    │ int[3] │  0x500C  │     40 │
    ├────────┼──────────┼────────┤
    │ int[4] │  0x5010  │     50 │
    └────────┴──────────┴────────┘
```

```C
int numbers[] = {10, 20, 30, 40, 50};
int *p = numbers;    /* p points to numbers[0] */

printf("%d\n", *p);       /* prints 10 */
printf("%d\n", p[0]);     /* also prints 10 */
printf("%d\n", numbers[0]); /* also also prints 10 */
```

The expression `p[0]` is just [syntactic sugar][syntactic-sugar] for
`*(p + 0)`. In fact, `p[n]` is equivalent to `*(p + n)`. The bracket
notation is a convenience for people who don't get pointers. But not
us, pointers are easy and we like to type.


## Pointer Arithmetic

Adding an integer to a pointer doesn't add that many _bytes_. It adds
that many _elements_, where the element size is determined by the
type the pointer points to.

```C
int numbers[] = {10, 20, 30, 40, 50};
int *p = numbers;

printf("%d\n", *(p + 0));    /* 10 */
printf("%d\n", *(p + 1));    /* 20 */
printf("%d\n", *(p + 2));    /* 30 */
```

If `int` is 4 bytes on your machine, then `p + 1` advances the actual
memory address by 4 bytes -- enough to land on the next integer in the
array. The compiler handles this scaling automatically. This is one of
those things that makes C both powerful and terrifying: the compiler
trusts you to stay inside the bounds of your array, and nothing stops
you from walking off the end into whatever happens to be next in
memory.

```C
printf("%d\n", *(p + 5));    /* whoops! indexed off the array */
```

That's reading past the end of the array. The compiler won't warn
you. The runtime won't stop you. You'll get whatever value happens to
be sitting in the next `sizeof(int)` bytes. Or a segfault. Or it'll
work fine in development and blow up in production at 3 AM on a
Saturday. That's the C experience of people with poor pointer hygiene.

## Pointers to Structures

Structures and pointers go together like `argc` and `argv`. You're
constantly passing pointers to structures, which means you're
constantly dereferencing them to access members:

```C
typedef struct {
    int   x;
    int   y;
    char *label;
} point_t;

point_t origin = { 0, 0, "origin" };
point_t *p = &origin;

printf("%s: (%d, %d)\n", (*p).label, (*p).x, (*p).y);
```

That `(*p).member` syntax is correct but ugly enough that C provides
the arrow operator as a mercy:

```C
printf("%s: (%d, %d)\n", p->label, p->x, p->y);
```

The `->` operator means "dereference the pointer on the left and
access the member on the right."

```
    Variable    Address    Value
    ┌────────┬──────────┬────────┐
    │point_t │  0x6000  │ 0x7000 │─ ─ ┐
    │ *p     │          │        │     │
    └────────┴──────────┴────────┘     │
                                       │
    ┌────────┬──────────┬────────┐     │
    │ .x     │  0x7000  │      0 │◄─ ─ ┘  p->x
    ├────────┼──────────┼────────┤
    │ .y     │  0x7004  │      0 │         p->y
    ├────────┼──────────┼────────┤
    │ .label │  0x7008  │ 0x2000 │─ ─ ▸ "origin"
    └────────┴──────────┴────────┘
```

You will use this operator constantly. It's the most common thing
you'll type after semicolons.

## **NULL**: The Billion Dollar Mistake

A pointer that doesn't point to anything should be set to **NULL**, cast
to the appropriate pointer type:

```C
int *p = (int *)NULL;
point_t *origin = (point_t *)NULL;
```

```
    Variable    Address    Value
    ┌────────┬──────────┬────────┐
    │ int *p │  0x4000  │ 0x0000 │─ ─ ▸ address zero
    └────────┴──────────┴────────┘      (no-access page)
```

**NULL** is typically a macro for zero, and address 0x0000 in your
[process's address space][address-space] is deliberately mapped with
no read or write permissions. Try to dereference it and the hardware
raises a fault, the operating system delivers a [SIGSEGV
signal][signals] to your process, and that's the end of that. The
_why_ of address zero being special is a topic for when we talk about
[memory layout][address-space] -- for now, just know that **NULL** means
"points to a place you're not allowed to touch."

[Sir Tony Hoare][hoare] called null references his "billion-dollar
mistake" and he's probably being modest about the dollar amount.

The good news is that **NULL** is something you can _check_ for:

```C
int do_something(int *data) {
    if (!data) {
        errno = EINVAL;
        return EXIT_FAILURE;
    }
    /* safe to dereference data now */
    return EXIT_SUCCESS;
}
```

Always validate pointers at function boundaries. I cannot stress this
enough. The 73 seconds you spend writing a **NULL** check will save you
three hours of debugging a core dump. I've done the math.

Some people think defensive **NULL** checking is "extra code" and
they're right. It is extra code. It's the extra code that stands
between your program and the sort of catastrophic failure that makes
sysadmins tear their hair and update their resumes. Think of the
sysadmins, check for **NULL**.

## Putting It Together

Here's a small program that uses everything we've talked about. It
builds an array of points, sorts them by distance from the origin
using a pointer-based comparison function, and prints the results. To
do the sorting, we're using a C standard library function named
[`qsort`][qsort-man-page] because implementing your own sort is just
asking for calls at 2AM from an irate manager who wants to know why
Zurich and Amsterdam are in the wrong places in a report. Oddly
specific, no?

Let's take a quick look at the `qsort` function prototype:

```C
void qsort(
    void *base, 
	size_t nel, 
	size_t width, 
	int (*compar)(const void *, const void *)
);
```

This incantation says `qsort` returns nothing and takes four
arguments, each doing a specific job:

- **`void *base`** -- a pointer to the beginning of the array you want
  sorted. It's `void *` because `qsort` doesn't know or care what
  type your array contains. Integers, structures, strings -- doesn't
  matter. It just sees bytes. This is the tradeoff `void *` offers:
  you get a function that works on _any_ data type, but the compiler
  can't check that you're using it correctly. That responsibility is
  yours.

- **`size_t nel`** -- the number of elements in the array. **Not** the
  number of bytes. `qsort` will do the byte math itself using...

- **`size_t width`** -- the size of each element in bytes. This is
  how `qsort` knows where one element ends and the next begins. You
  almost always pass `sizeof(your_type)` here.

- **`int (*compar)(const void *, const void *)`** -- and then finally
  a bit of black magic called a function pointer. This is how you
  tell `qsort` what "sorted" means for your data.

Let's break down that function pointer declaration even further.

```C
int              /* return type of the function */
(*compar)        /* a function pointer named "compar" */
(                /* that takes two arguments: */
  const void *,  /* a pointer to unspecified read-only data */
  const void *   /* a second pointer to unspecified read-only data */
)                /* end of the function pointer's arguments */
```

The declaration for `compar`, which is short for comparison, means
that `qsort` is asking the caller to pass in a function that returns an
integer and takes two void pointers as arguments. The `const` is a promise
that the comparison function won't modify the data being compared --
it's just looking, not touching.

Here's the complete program:

```C
/* points.c */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

typedef struct {
    double x;
    double y;
    char   name[32];
} point_t;

#define POINT_SENTINEL { 0.0, 0.0, "" }

double distance(const point_t *p);
int    compare_points(const void *a, const void *b);

int main(int argc, char *argv[]) {
    point_t cities[] = {
        { 3.0,  4.0,  "Springfield" },
        { 1.0,  1.0,  "Shelbyville" },
        { 10.0, 10.0, "Capital City" },
        { 0.5,  0.5,  "Ogdenville" },
        POINT_SENTINEL,                 /* marks end of array */
    };

    int n = sizeof(cities) / sizeof(cities[0]) - 1;  /* exclude sentinel */

    qsort(cities, n, sizeof(point_t), compare_points);

    for (point_t *p = cities; *p->name != '\0'; p++) {
        printf("%-15s (%.1f, %.1f) distance: %.2f\n",
               p->name,
               p->x,
               p->y,
               distance(p));
    }

    return EXIT_SUCCESS;
}

double distance(const point_t *p) {
    if (!p) return 0.0;
    return sqrt(p->x * p->x + p->y * p->y);
}

int compare_points(const void *a, const void *b) {
    double da = distance((const point_t *)a);
    double db = distance((const point_t *)b);

    if (da < db)
        return -1;
    if (da > db)
        return 1;
    return 0;
}
```

Compile and run:

```console
$ gcc -o points points.c -lm
$ ./points
Ogdenville      (0.5, 0.5) distance: 0.71
Shelbyville     (1.0, 1.0) distance: 1.41
Springfield     (3.0, 4.0) distance: 5.00
Capital City    (10.0, 10.0) distance: 14.14
```

Look at what's happening with pointers in this program:

- `distance()` takes a pointer to a `point_t` so it doesn't copy the struct
- `compare_points()` receives `void *` pointers from `qsort()` and casts them to `const point_t *` so it can access the actual data
- `qsort()` sorts the array in place using our comparison function
- The `for` loop iterates with a pointer, stepping through the array
  until it hits the sentinel -- an entry with an empty name that marks
  the end. This is a common C pattern: rather than tracking array
  length separately, you put a recognizable "stop" value at the end.
  Strings work the same way with their `'\0'` terminator
- Every structure access uses `->` because we're working through pointers

Yes, this is magic. Strong potent C magic. The `qsort()` function
doesn't know anything about our `point_t` structure -- it just
shuffles bytes around according to whatever comparison function we
hand it, and we hand it that function as a _pointer_. As you begin
to internalize how this works you'll find more opportunities to use
techniques like this in your own code. Things like linked lists, hash
tables, and callback-driven architectures stop being mysterious and
start being tools you reach for.

## Where To Go From Here

This article covered the fundamentals: what pointers are, how to use
them, and why they matter. There's more -- dynamic memory allocation
with `malloc()` and `free()`, and pointer-to-pointer indirection for
when you need to modify a pointer itself. I think your head is probably
spinning enough for the time being so we'll save those topics for later.

For now, go write a program that uses pointers. Write one that
crashes. Figure out why it crashed. Write another one. The fastest way
to get comfortable with pointers is to use them badly, then use them
better.

Go write something cool (with pointers)!

<!-- Links -->
[segfault]: signals-and-segfaults
[how-i-write-main]: ../how-i-write-main/article.md
[names-and-spaces]: more-tales-from-the-land-of-the-linker-aliens
[linker-aliens]: XX-my-time-among-the-linker-aliens
[address-space]: process-address-space-and-memory-layout
[hoare]: https://en.wikipedia.org/wiki/Tony_Hoare#Apologies_and_retractions
[signals]: oh-boy-this-is-a-doozie
[syntactic-sugar]: https://en.wikipedia.org/wiki/Syntactic_sugar
[qsort-man-page]: https://man7.org/linux/man-pages/man3/qsort.3.html
