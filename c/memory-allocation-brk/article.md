<!--
Author: Erik O'Shaughnessy
Editor: Claude
Date: November 2026
Status: draft
Series: C Programming
Prerequisites: address-space
Next: memory-allocation
-->

# Moving the Edge: brk, sbrk, and the Simplest Allocator

Every memory allocator you will ever use is built on a handful of ideas,
and the oldest of them is small enough to fit on one screen. The
**HEAP** has an edge, and you move it. There are no free lists and no
bookkeeping, because there is only one edge. Moving the edge is also the
best way I know to understand why the allocators we use today look the
way they do.

**Me**: a Unix programmer with a soft spot for system calls that do
exactly one thing.

**You**: someone who has read [a map of memory][address-space] and wants
to know what actually moves when the **HEAP** grows.

Let's move the edge.

## The Edge

In the beginning, Unix system programmers got more memory by invoking a
three-letter incantation: [`brk()`][brk]. The **HEAP** ends at a line
called the _program break_. Move the line up and the kernel hands you
the pages in between. Move it back down and you've given them back. The
call `brk()` sets the break to an address you choose, and its sibling
`sbrk()` moves it by an amount and returns where it used to be.

Here is what happens when you ask `sbrk()` for 4096 bytes. The edge
climbs, and the bytes it climbed over are yours. I've tidied the
addresses so the arithmetic is easy to see:

```
    Before sbrk(4096)                           After sbrk(4096)
    ┌───────────────────┐                       ┌───────────────────┐
    │     (unmapped)    │                       │     (unmapped)    │
    │                   │                       ├───────────────────┤ ◄─ edge 0x6000
    │                   │                       │   new 4096 bytes  │
    ├───────────────────┤ ◄─ edge 0x5000        ├───────────────────┤ ◄─ old edge 0x5000
    │        HEAP       │                       │        HEAP       │
    └───────────────────┘                       └───────────────────┘
```

Here is the whole thing in C:

```C
/* brk.c - the simplest allocator there is: move the edge of the HEAP */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(void) {
    void *start = (void *)NULL;
    char *block = (char *)NULL;
    void *end = (void *)NULL;

    start = sbrk(0);
    if ((block = (char *)sbrk(4096)) == (char *)-1) {
        perror("block");
        return EXIT_FAILURE;
    }
    strcpy(block, "hello from the edge");
    end = sbrk(0);

    printf("the edge was at  %p\n", start);
    printf("sbrk(4096) gave  %p  \"%s\"\n", (void *)block, block);
    printf("the edge is now  %p\n", end);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o brk brk.c
$ ./brk
the edge was at  0x27ea1000
sbrk(4096) gave  0x27ea1000  "hello from the edge"
the edge is now  0x27ea2000
```

The call `sbrk()` returns the old edge, and that is where your new
memory begins, which is why the first two lines match. The third line
shows the edge 4096 bytes higher. On failure it returns `(void *)-1`, an
odd choice for a pointer, so that's what the check looks for. I read all
three values before printing any of them, because the first `printf()`
allocates a buffer for stdout and moves the edge by 132 KB all by
itself.

Those 132 KB are the same size the **HEAP** was in [a map of
memory][address-space], and now you know where that number came from.
System calls are expensive, so glibc asks for a cushion of 128 KB on top
of whatever you requested, rounded up to whole pages, and parcels it out
from there. The cushion is documented in [mallopt(3)][mallopt] as
`M_TOP_PAD`.

A word of caution before you try this at home. The call `sbrk()` was
retired from POSIX years ago, and `malloc()` expects to be the one
moving the edge. Treat this program as a demonstration and leave the
edge to `malloc()` in real code.

## Giving It Back

Giving memory back means calling `sbrk()` with a negative number.
`sbrk(-4096)` puts the edge where it was. That's the whole interface,
and it's also the limit. You can only lower the edge, so you can only
give back what you took last. Giving memory back behaves like a stack,
last in and first out.

Take three allocations, A then B then C, each one above the last. Now
free B:

```
    Three allocations            After free(B)
    ┌─────────────┐              ┌─────────────┐
    │  (unmapped) │              │  (unmapped) │
    ├─────────────┤ ◄─ edge      ├─────────────┤ ◄─ edge, stuck above C
    │      C      │              │      C      │
    ├─────────────┤              ├─────────────┤
    │      B      │              │    (hole)   │
    ├─────────────┤              ├─────────────┤
    │      A      │              │      A      │
    └─────────────┘              └─────────────┘
```

There is a hole where B was, and nothing can fill it. The edge can't
come down to reclaim the space, because C is sitting above it and the
edge would take C along. Freeing from the middle is the problem every
other allocator exists to solve.

## A Very Small Allocator

You can see the whole idea in a function. This one hands out memory by
moving the edge and never takes any of it back:

```C
/* bump.c - the simplest possible allocator: it only goes up */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void *bump(size_t size);

int main(void) {
    size_t sizes[3] = { 10, 100, 1 };
    void *blocks[3] = { (void *)NULL, (void *)NULL, (void *)NULL };

    for (size_t i = 0; i < 3; i++) {
        if (!(blocks[i] = bump(sizes[i]))) {
            perror("blocks");
            return EXIT_FAILURE;
        }
    }
    for (size_t i = 0; i < 3; i++)
        printf("bump(%3zu) -> %p\n", sizes[i], blocks[i]);
    return EXIT_SUCCESS;
}

void *bump(size_t size) {
    void *block = (void *)NULL;

    if (size == 0) {
        errno = EINVAL;
        return (void *)NULL;
    }
    size = (size + 15) & ~(size_t)15;
    if ((block = sbrk((intptr_t)size)) == (void *)-1)
        return (void *)NULL;
    return block;
}
```

```console
$ gcc -Wall -o bump bump.c
$ ./bump
bump( 10) -> 0x1f89a000
bump(100) -> 0x1f89a010
bump(  1) -> 0x1f89a080
```

Each block begins where the edge was. The first is 16 bytes long even
though I asked for 10, because `bump()` rounds every request up to a
multiple of 16. That keeps each block aligned for any type the compiler
might put in it, and 16 is what `malloc()` on 64-bit glibc promises too.
The second begins 16 bytes after the first and the third begins 112
after that, which is the 100 bytes I asked for, rounded up.

There's no bookkeeping anywhere, which is why this fits on a screen. It
also means that `bump()` can't tell you how big a block is, and it has
no way to give one back.

## What the Real Ones Do

Every problem `bump()` has is a problem a real allocator solves, and the
solutions are the numbers you'll meet in [borrowing
memory][memory-allocation].

A hole like B's has to be remembered and reused, which means keeping a
list of free blocks and writing down how big each one is. That's what
the bookkeeping in front of every glibc block is for, and it's part of
why the smallest block you can get is 24 bytes. Going back to the kernel
for every request is slow, so the allocator takes a big chunk and hands
it out in pieces. That's the 128 KB cushion. And a very large block is
better off in a mapping of its own, where it can be returned without
caring what sits above it. That's the threshold where `malloc()` stops
using the edge altogether.

None of that needs to be mysterious. You've already seen the problem it
solves.

## Where To Go From Here

Both programs here fit on a screen, so type them in. Then change them.
Print the edge before and after every call to `bump()`. Allocate a
million one-byte blocks and watch how far the edge moves. Write a
`bump_free()` that gives the last block back by moving the edge down,
then call it on the middle block and see what breaks.

When you're ready for an allocator that can free from the middle, it's
waiting in [borrowing memory][memory-allocation].

Go move the edge, and bring it back.

<!-- Links -->
[address-space]: ../address-space/article.md
[memory-allocation]: ../memory-allocation/article.md
[brk]: https://man7.org/linux/man-pages/man2/brk.2.html
[mallopt]: https://man7.org/linux/man-pages/man3/mallopt.3.html
