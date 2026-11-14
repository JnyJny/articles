<!--
Author: Erik O'Shaughnessy
Editor: Claude
Date: November 2026
Status: draft
Series: C Programming
Prerequisites: address-space
Next: pointer-pitfalls
-->

# Borrowing Memory: malloc, free, and the Rest of the Family

Sooner or later your program needs a block of memory whose size depends
on something it only learns while running, like how many bytes are in
the file you want to read. If the file never changes, you can hard code
the size in an array and drive on. But if the file changes, you've got
to figure out how to get enough memory to hold it. And like programs,
files never stay small. In this article we're going to talk about
dynamic memory allocation in C, and by the end you'll have a better
understanding of how to ask the computer for memory, how to give it back
and what goes wrong if you mess it up.

I'm writing for someone who has read [a map of memory][address-space]
and is ready to start putting things on the **HEAP**. I've made most of
the mistakes you're about to make, so you don't have to.

Let's borrow some memory.

## Which Allocator?

First, there is no such thing as _the_ memory allocator. There are
algorithms for handing out memory, and there are implementations of
them, and the implementations disagree about the details.

This article is about one of those implementations: the allocator in
[glibc][link-to-glibc-docs], the [C library][future-libc-article] on
most Linux systems, because that's where every example here was run. The
interface belongs to the C standard, so `malloc()`, `calloc()` and
`free()` mean the same thing everywhere. What happens underneath is
glibc's own spin on how to implement the standard: how much memory you
really get, where it comes from, what is in it when it arrives. If your
system has a different allocator, run the examples and compare notes.

If you want to meet one of the oldest and simplest allocators, an
introduction to the dark magic of `brk()` can be found in [moving the
edge][memory-allocation-brk].

## Read The "Fine" Manual

Second, nobody is born knowing the C API. In Unix derived operating
systems, like Linux, we use the manual pages to get implementation
details of the library functions and system calls we'd like to use.

Everything in this article has a manual page, and you can read it
without leaving the terminal. Try `man malloc`. How a page gets picked
when a name appears in more than one section varies from one Unix to the
next, so [`man man`][man-man] is the page to read first.

When a page opens, skim it in this order. SYNOPSIS shows the function's
signature and the header you need to include. RETURN VALUE says what you
get back when things go wrong, which for `malloc()` is the **NULL**
you've been checking for. ERRORS, where a page has one, lists the values
`errno` can hold. SEE ALSO is a map of where to go next. The pages I
lean on here are linked, so you can read them in a browser too.

## A Gentle Admonition

Finally, every program in this article is short enough to type in a
couple of minutes, and I'd like you to type them. As a kid I typed in
programs from Dr. Dobb's Journal. Reading about code can feel passive
and typing it in doesn't. Cut and paste is a thing, but give it a rest.
Type it, compile it, run it, and then change something. Predict what
will happen and the result that surprises you is the one you'll
remember.

## Ask, Check, Give Back

Every piece of C that allocates memory and _works_ does three things:

1. Asks the allocator for a block.
1. Checks that the allocator said yes.
1. Gives the block back when it's finished.

Missing one of those things changes the "_works_" part for the worse.

Here are all three steps in one small program. It takes a number from
the command line, allocates memory for that many `int`s, fills them with
squares, and adds them up:

```C
/* numbers.c - allocate an array whose size is chosen at runtime */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    size_t count = 10;
    int *squares = (int *)NULL;
    long total = 0;

    if (argc > 1)
        count = strtoul(argv[1], (char **)NULL, 10);

    if (!(squares = (int *)malloc(count * sizeof(*squares)))) {
        fprintf(stderr, "could not allocate %zu ints\n", count);
        return EXIT_FAILURE;
    }

    for (size_t i = 0; i < count; i++) {
        squares[i] = (int)(i * i);
        total += squares[i];
    }

    printf("%zu squares sum to %ld\n", count, total);

    free(squares);

    return EXIT_SUCCESS;
}
```

I know that `if` packs a lot into one line. Take it apart from the
inside out:

- `count * sizeof(*squares)` is the number of bytes to ask for
- `(int *)malloc(...)` asks the allocator for that many bytes and casts
  the answer to the pointer type we want
- `squares = ...` stores the answer in `squares`. An assignment is also
  an expression, and its value is the value it stored
- `!(...)` is true when that value is **NULL**, so the body of the `if`
  runs only when the allocation failed

Compile it and try a few counts:

```console
$ gcc -Wall -o numbers numbers.c
$ ./numbers
10 squares sum to 285
$ ./numbers 1000
1000 squares sum to 332833500
$ ./numbers 99999999999999
could not allocate 99999999999999 ints
```

The function `malloc()` takes a number of bytes and returns a pointer to
the first one, or **NULL** if the allocator can't satisfy the request.
That last run asked for about 400 terabytes, which is more than a
typical machine can give a process, and `malloc()` said no. Check the
return value of `malloc()` every time. The one time you skip it will
result in someone calling you at 4am and asking you why your program
crashed and the downtime is costing real money. Nobody likes those
calls.

Notice I wrote the size as `count * sizeof(*squares)` and not
`count * sizeof(int)`. The expression `*squares` has whatever type
`squares` points at, so if the new guy changes the declaration to
`long`, the allocation follows along without anybody remembering to edit
it. I cast the return value of `malloc()` to the pointer type, the same
way I cast **NULL**, because I like it when types agree with each other.
The C language doesn't require it, but it signals the writer's
intention. The function returns a `void *`, which converts to any
pointer type on its own.

When you're finished with the block, you pass the pointer to `free()`,
exactly as `malloc()` gave it to you, once. Passing **NULL** to `free()`
is allowed and does nothing, which makes cleanup code shorter than it
would otherwise be.

Why bother giving it back? Because of where the pieces live. Take a
function that sets `int *p` with `p = (int *)malloc(sizeof(*p));` and
stores 42 in the block. The pointer `p` is an ordinary variable on the
**STACK**. The block it points at lives on the **HEAP**. While the
function runs, you have both:

```
    Region   Variable    Address    Value
    ┌───────┬───────────┬──────────┬────────┐
    │ STACK │ int *p    │  0x7FF0  │ 0x5000 │─ ─ ─┐
    ├───────┼───────────┼──────────┼────────┤     │
    │ HEAP  │ p[0]      │  0x5000  │     42 │◄─ ──┘
    └───────┴───────────┴──────────┴────────┘
```

Then the function returns without calling `free()`. The frame on the
**STACK** is popped and its contents are up for grabs. The block on the
**HEAP** stays exactly where it was, still marked as in use, with
nothing left that knows its address:

```
    Region   Variable    Address    Value
    ┌───────┬───────────┬──────────┬────────┐
    │ STACK │ (popped)  │          │        │
    ├───────┼───────────┼──────────┼────────┤
    │ HEAP  │ p[0]      │  0x5000  │     42 │
    └───────┴───────────┴──────────┴────────┘
```

That's a _leak_. The allocator can't reuse the block because you haven't
said you're done with it, and you can't free it because you've lost its
address. The **HEAP** is an exquisite garden and you have to tend to it.

## What Is In a New Block?

Nothing you can rely on. The function `malloc()` doesn't clear the block
it returns. You get whatever the previous use of that region left
behind. To illustrate, I filled a block with the character `E`, freed
it, and asked for another one the same size:

```C
/* stale.c - what is in a fresh block? */
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char *first = (char *)NULL;
    char *second = (char *)NULL;

    if (!(first = (char *)malloc(64))) {
        perror("first");
        return EXIT_FAILURE;
    }

    memset(first, 'E', 64);

    free(first);

    if (!(second = (char *)malloc(64))) {
        perror("second");
        return EXIT_FAILURE;
    }

    for (int i = 0; i < 64; i++)
        fputc(isprint((unsigned char)second[i]) ? second[i] : '.', stdout);

    fputc('\n', stdout);

    free(second);

    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o stale stale.c
$ ./stale
................EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
```

The dots are bytes that aren't printable. The allocator scribbled its
own bookkeeping over the first 16, and the other 48 are still full of
`E`. Those 16 change from run to run, so now and then one of them shows
up as a printable character. Reading a block before you've written to it
is the thing you shouldn't do in real code, and I did it on purpose so
you could see what's there. Another allocator will leave something else
behind.

Leftover data is how secrets escape. A program reads a password into a
buffer and frees the buffer. Somewhere else, a different part of the
program asks for a block of the same size and gets the password back,
unasked.

## calloc: The Zeroed Block

If you want zeros, ask for zeros. The function `calloc()` allocates a
block and clears it, and it takes the number of elements and the size of
each as two separate arguments:

```C
table = (int *)calloc(count, sizeof(*table));
```

Zeroing sounds like extra work, but it can be free. For large blocks the
allocator can get fresh pages from the kernel, which hands them over
already zeroed, the same trick that makes **BSS** cheap. In that case
`calloc()` skips the clearing.

The two-argument form is more than a matter of taste. It lets `calloc()`
check the multiplication, which `malloc()` can't do because you already
did it. Here is what happens when the multiplication goes wrong:

```C
/* overflow.c - malloc() multiplies for you, calloc() checks the answer */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t count = (SIZE_MAX / sizeof(int)) + 1;    /* more ints than C can represent */
    int *by_malloc = (int *)NULL;
    int *by_calloc = (int *)NULL;

    printf("count * sizeof(int) = %zu\n", count * sizeof(int));

    if (!(by_malloc = (int *)malloc(count * sizeof(*by_malloc)))) {
        perror("by_malloc");
        return EXIT_FAILURE;
    }
    printf("malloc gave us %p\n", (void *)by_malloc);

    if (!(by_calloc = (int *)calloc(count, sizeof(*by_calloc)))) {
        perror("by_calloc");
        free(by_malloc);
        return EXIT_FAILURE;
    }
    printf("calloc gave us %p\n", (void *)by_calloc);

    free(by_malloc);
    free(by_calloc);

    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o overflow overflow.c
$ ./overflow
count * sizeof(int) = 0
malloc gave us 0x12f992b0
by_calloc: Cannot allocate memory
```

The computed size, `count * sizeof(int)`, wrapped around to zero, and
`malloc(0)` gleefully returned a pointer to a block that can hold
nothing. The code after it would go on believing it owned 4.6
quintillion `int`s. Believing you own more memory than you do is how
heap overflows start. The function `calloc()` noticed the overflow and
returned **NULL**, and the check turned that into an error message and a
failing exit. And gcc, even with `-Wall`, had nothing to say about any
of it.

## Where the Bytes Come From

[A map of memory][address-space] ended with a challenge: `malloc()` a
megabyte and see whether the address looks like the **HEAP** or like the
memory-mapped regions. This program allocates four blocks of different
sizes, prints where they landed, and then prints the range of the
`[heap]` mapping from `/proc/self/maps`:

```C
/* source.c - where do blocks of different sizes come from? */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    size_t sizes[4] = { 100, 100000, 200000, 1000000 };
    void *blocks[4] = {
        (void *)NULL, (void *)NULL, (void *)NULL, (void *)NULL
    };
    unsigned long low = 0;
    unsigned long high = 0;
    char line[256];
    FILE *maps = (FILE *)NULL;

    if (!(maps = fopen("/proc/self/maps", "r"))) {
        perror("maps");
        return EXIT_FAILURE;
    }

    for (size_t i = 0; i < 4; i++) {
        if (!(blocks[i] = malloc(sizes[i]))) {
            perror("blocks");
            return EXIT_FAILURE;
        }
        printf("malloc(%7zu) -> %#014lx\n", sizes[i], (unsigned long)blocks[i]);
    }

    while (fgets(line, sizeof(line), maps)) {
        if (strstr(line, "[heap]") != (char *)NULL &&
            sscanf(line, "%lx-%lx", &low, &high) == 2)
            printf("[heap] is %#014lx-%#014lx\n", low, high);
    }
    fclose(maps);

    for (size_t i = 0; i < 4; i++)
        free(blocks[i]);

    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o source source.c
$ ./source
malloc(    100) -> 0x00000610d480
malloc( 100000) -> 0x00000610e500
malloc( 200000) -> 0xffff876ef010
malloc(1000000) -> 0xffff875fa010
[heap] is 0x00000610d000-0x00000612e000
```

The first two blocks sit inside the `[heap]` range. The last two are far
away, up in the memory-mapped region. By default glibc serves requests
under 128 KB from the **HEAP**, the part that grows by [moving the
edge][memory-allocation-brk], and anything at or above that gets a
mapping of its own through `mmap()`. A block with its own mapping can be
handed straight back to the kernel when you free it. The 128 KB
threshold is glibc's default, documented in [mallopt(3)][mallopt], and
glibc adjusts it as the program runs. Other allocators draw the line
somewhere else.

## What You Asked For and What You Got

You'll also get more than you asked for, because the allocator rounds
every request up. Using glibc you can ask what a block really holds with
`malloc_usable_size()`. It's a glibc extension, so don't put it in
anything you plan to port:

```C
/* usable.c - ask the allocator how much it really gave us (glibc) */
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t asked[] = { 1, 4, 24, 25, 100, 1000 };

    for (size_t i = 0; i < sizeof(asked) / sizeof(asked[0]); i++) {
        void *block = (void *)NULL;

        if (!(block = malloc(asked[i]))) {
            perror("block");
            return EXIT_FAILURE;
        }
        printf("asked for %4zu, got %4zu usable bytes\n", asked[i],
               malloc_usable_size(block));
        free(block);
    }
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o usable usable.c
$ ./usable
asked for    1, got   24 usable bytes
asked for    4, got   24 usable bytes
asked for   24, got   24 usable bytes
asked for   25, got   40 usable bytes
asked for  100, got  104 usable bytes
asked for 1000, got 1000 usable bytes
```

I asked for one byte and got twenty-four, which means a million tiny
allocations cost many times more than a million bytes. Keep that in mind
when you're tempted to allocate small things one at a time.

## The Rest of the Family

You've met the main characters. A few more are worth knowing:

| Function                         | What it does                           |
|----------------------------------|----------------------------------------|
| `malloc(size)`                   | A block of `size` bytes, not cleared   |
| `calloc(count, size)`            | A zeroed block, multiply checked       |
| `realloc(ptr, size)`             | Resize a block, maybe moving it        |
| `reallocarray(ptr, count, size)` | `realloc()` with the multiply checked  |
| `aligned_alloc(alignment, size)` | A block starting on an aligned address |
| `strdup(text)`                   | Allocate a copy of a string            |
| `free(ptr)`                      | Give a block back; **NULL** is fine    |

Some of these have fine print. The function `realloc()` resizes a block
and may move it. I almost never use it, so I'll leave it to the [man
page][malloc-man]. If you do reach for it when growing an array,
`reallocarray()` gives it the overflow check that `calloc()` has. It
isn't part of the C standard, but glibc and the BSDs have it. The
function `aligned_alloc()` arrived in C11 for hardware that wants data
on particular boundaries, such as vector instructions. The function
`strdup()` is POSIX and joined the C standard in C23. It allocates room
for the string and its terminator, copies it, and hands you the result.
You free it like anything else.

There is also `alloca()`, which allocates on the **STACK** and releases
the memory when the function returns, with no `free()`. `alloca()`
sounds like the end of the allocation problem, and I thought so too. I
used it a lot until I realized what it was costing me: memory with two
sets of rules, and no way to tell by looking at a pointer which set
applied. Hand that memory to `free()` and, if you're lucky, glibc stops
the program with `double free or corruption (out)`. gcc will warn you
before it ever runs. Keep the pointer after the function returns and it
points into a **STACK** frame that is no longer yours.

## Putting It Together

Here is a program that uses `malloc()`, `strdup()` and `free()`
together. It reads lines from standard input into a stack implemented
with a linked list, one node per line, and prints them in reverse. Each
new node goes on top of the stack, so the last line read comes out
first:

```C
/* lines.c - read lines from stdin, print them in reverse */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct line {
    char *text;
    struct line *next;
} line_t;

int line_push(line_t **head, const char *text);
void line_free_all(line_t *head);

int main(int argc, char *argv[]) {
    line_t *head = (line_t *)NULL;
    line_t *node = (line_t *)NULL;
    char buffer[256];

    while (fgets(buffer, sizeof(buffer), stdin)) {
        buffer[strcspn(buffer, "\n")] = '\0';
        if (line_push(&head, buffer) != EXIT_SUCCESS) {
            line_free_all(head);
            return EXIT_FAILURE;
        }
    }
    for (node = head; node; node = node->next)
        printf("%s\n", node->text);

    line_free_all(head);
    return EXIT_SUCCESS;
}

int line_push(line_t **head, const char *text) {
    line_t *node = (line_t *)NULL;

    if (!head || !text) {
        errno = EINVAL;
        return EXIT_FAILURE;
    }

    if (!(node = (line_t *)malloc(sizeof(*node)))) {
        perror("node");
        return EXIT_FAILURE;
    }

    if (!(node->text = strdup(text))) {
        perror("text");
        free(node);
        return EXIT_FAILURE;
    }

    node->next = *head;

    *head = node;

    return EXIT_SUCCESS;
}

void line_free_all(line_t *head) {
    line_t *next = (line_t *)NULL;

    while (head) {
        next = head->next;
        free(head->text);
        free(head);
        head = next;
    }
}
```

```console
$ gcc -Wall -o lines lines.c
$ printf 'one\ntwo\nthree\nfour\nfive\nsix\n' | ./lines
six
five
four
three
two
one
```

Every allocation in this program has exactly one matching `free()`:

- `line_push()` makes two allocations for each line: one for the node,
  and one for the copy of the text that `strdup()` makes
- if the copy fails, it frees the node before returning, so a failure
  never leaks
- `line_free_all()` frees each node's text before it frees the node,
  because the node holds the only pointer to the text
- it saves `next` before freeing the node, since nothing is allowed to
  touch a node after it's freed

I also compiled it once with `-fsanitize=address`, a gcc option that
catches leaks and bad memory accesses, and it had nothing to say. That
option gets a proper introduction in [pointer
pitfalls][pointer-pitfalls].

## Now Break It

Take `lines.c` and break it three ways. Take out the `free(head->text)`
in `line_free_all()`. Read a node's `next` after you free the node.
Remove the `free(node)` on the `strdup()` failure path. Before you run
each one, predict what will happen.

Then change it. Read numbers and sum them. Keep the lines in the order
they arrived. Print the address of every node and see how far apart they
land. Then write something of your own that allocates, and count the
`malloc()`s and the `free()`s. When the two numbers disagree, you have a
leak. What happens when they disagree in other ways is the subject of
[pointer pitfalls][pointer-pitfalls].

Go borrow some memory and then give it back.

<!-- Links -->
[address-space]: ../address-space/article.md
[pointer-pitfalls]: ../pointer-pitfalls/article.md
[mallopt]: https://man7.org/linux/man-pages/man3/mallopt.3.html
[malloc-man]: https://man7.org/linux/man-pages/man3/malloc.3.html
[memory-allocation-brk]: ../memory-allocation-brk/article.md
[link-to-glibc-docs]: https://www.gnu.org/software/libc/manual/
[future-libc-article]: ../standard-library/article.md
[man-man]: https://man7.org/linux/man-pages/man1/man.1.html
