<!--
Author: Erik O'Shaughnessy
Editor: Johnny (Jny)
Date: November 2026
Status: draft
Series: C Programming
Prerequisites: address-space
Next: pointer-pitfalls
-->

# Borrowing Memory: malloc, free, and the Rest of the Family

Sooner or later your program needs a block of memory whose size depends
on something it only learns while running. How many lines are in the
file? How many users connected? How long is the string the network just
handed you? The compiler can't know, and an array on the **STACK**
vanishes the moment its function returns. So you ask for memory from the
**HEAP**, use it, and give it back. The asking is easy. The giving back
is where programs go wrong.

**Me**: a Unix programmer who counts `malloc()` calls the way other
people count calories.

**You**: someone who has read [the map of memory][address-space] and is
ready to start putting things on the **HEAP**.

Let's borrow some memory.

## Ask, Check, Give Back

Every piece of C that allocates memory and works does three things:

- asks the allocator for a block
- checks that the allocator said yes
- gives the block back when it's finished

Here is all three in one small program. It takes a count from the
command line, allocates room for that many `int`s, fills them with
squares, and adds them up:

```C
/* numbers.c - allocate an array whose size is chosen at runtime */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    size_t count = 10;
    int *squares = (int *)NULL;
    long total = 0;

    if (argc > 1) {
        count = strtoul(argv[1], (char **)NULL, 10);
    }

    squares = malloc(count * sizeof(*squares));
    if (squares == (int *)NULL) {
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
the first one, or **NULL** if it can't oblige. That last run asked for
about 400 terabytes, which is more than any address space holds, and
`malloc()` said no. Check for that every time. The one time it matters
will be the time you skipped it.

I write the size as `count * sizeof(*squares)` and never as
`count * sizeof(int)`. The expression `*squares` has whatever type
`squares` points at, so if someone changes the declaration to `long`,
the allocation follows along without anybody remembering to edit it.
You'll also notice there's no cast on the return value of `malloc()`. It
returns a `void *`, which C converts to any pointer type on its own, so
a cast only adds noise.

When you're finished with the block, you pass the pointer to `free()`,
exactly as `malloc()` gave it to you, once. Passing it **NULL** is
allowed and does nothing, which makes cleanup code shorter than it would
otherwise be.

Why bother giving it back? Because of where the pieces live. Take a
function that does `int *p = malloc(sizeof(*p));` and stores 42 in the
block. The pointer `p` is an ordinary variable on the **STACK**. The
block it points at lives on the **HEAP**. While the function runs, you
have both:

```
    Region   Variable    Address    Value
    ┌───────┬───────────┬──────────┬────────┐
    │ STACK │ int *p    │  0x7FF0  │ 0x5000 │─ ─ ┐
    ├───────┼───────────┼──────────┼────────┤     │
    │ HEAP  │ p[0]      │  0x5000  │     42 │◄─ ─ ┘
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
address. Nobody cleans up the **HEAP** for you.

## What Is in a New Block?

Nothing you can rely on. The function `malloc()` doesn't clear the block
it returns. You get whatever the previous tenant left behind. To see it,
I filled a block with `A`, freed it, and asked for another one the same
size:

```C
/* stale.c - what is in a fresh block? */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char *first = malloc(64);
    char *second = (char *)NULL;

    memset(first, 'A', 64);
    free(first);

    second = malloc(64);
    for (int i = 0; i < 64; i++) {
        putchar((second[i] >= ' ' && second[i] < 127) ? second[i] : '.');
    }
    putchar('\n');
    free(second);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o stale stale.c
$ ./stale
................AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
```

The dots are bytes that aren't printable. The allocator scribbled its
own bookkeeping over the first 16, and the other 48 are still full of
`A`. Reading a block before you've written to it is the thing you
shouldn't do in real code, and I did it on purpose so you could see
what's there. Another allocator will leave something else behind.

This is how secrets escape. A program reads a password into a buffer and
frees the buffer. Somewhere else, a different part of the program asks
for a block of the same size and gets the password back, unasked.

## calloc: The Zeroed Block

If you want zeros, ask for zeros. The function `calloc()` allocates a
block and clears it, and it takes the number of elements and the size of
each as two separate arguments:

```C
int *table = calloc(count, sizeof(*table));
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
    size_t count = (SIZE_MAX / sizeof(int)) + 1;    /* more ints than can exist */
    int *by_malloc = malloc(count * sizeof(*by_malloc));
    int *by_calloc = calloc(count, sizeof(*by_calloc));

    printf("count * sizeof(int) = %zu\n", count * sizeof(int));
    printf("malloc gave us %p\n", (void *)by_malloc);
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
malloc gave us 0xf1662a0
calloc gave us (nil)
```

The product wrapped around to zero, and `malloc(0)` cheerfully returned
a pointer to a block that can hold nothing. The code after it would go
on believing it owned 4.6 quintillion `int`s. That is how heap overflows
start. The function `calloc()` noticed the overflow and returned
**NULL**. And gcc, even with `-Wall`, had nothing to say about any of
it.

## realloc: Changing Your Mind

The function `realloc()` resizes a block. Give it a pointer from the
allocator and a new size, and it returns a pointer to a block of the new
size with your old contents copied over. The returned pointer may be the
same as the one you passed in, or it may not. That has two consequences.

First, use the pointer `realloc()` returns and forget the one you had.
Second, when `realloc()` fails it returns **NULL** and leaves your old
block untouched, still allocated, still yours. That makes the natural
way to write it a trap:

```C
items = realloc(items, bigger * sizeof(*items));    /* if this fails, items is lost */
```

On failure, that line overwrites your only pointer to the old block with
**NULL**. You've leaked the block, and the next line that touches
`items` is a crash. The cure is a temporary, and it's the pattern I use
every time:

```C
/* grow.c - watch a block move as it grows */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t capacity = 4;
    int *items = malloc(capacity * sizeof(*items));

    if (items == (int *)NULL) {
        return EXIT_FAILURE;
    }

    for (size_t used = 0; used < (1UL << 15); used++) {
        if (used == capacity) {
            uintptr_t before = (uintptr_t)items;
            int *bigger = realloc(items, 2 * capacity * sizeof(*items));

            if (bigger == (int *)NULL) {
                free(items);
                return EXIT_FAILURE;
            }
            printf("%8zu ints: %#lx -> %#lx%s\n", capacity, (unsigned long)before,
                   (unsigned long)(uintptr_t)bigger,
                   ((uintptr_t)bigger == before) ? "  (stayed put)" : "");
            items = bigger;
            capacity *= 2;
        }
        items[used] = (int)used;
    }

    free(items);
    return EXIT_SUCCESS;
}
```

This program fills an array and doubles it whenever it runs out of room,
printing where the block was before and after each growth. I save the
old address as an integer before calling `realloc()`, because once a
block has moved, the old pointer isn't something you should even
compare.

```console
$ gcc -Wall -o grow grow.c
$ ./grow
       4 ints: 0x18fd02a0 -> 0x18fd02a0  (stayed put)
       8 ints: 0x18fd02a0 -> 0x18fd12e0
      16 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
      32 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
      64 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
     128 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
     256 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
     512 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
    1024 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
    2048 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
    4096 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
    8192 ints: 0x18fd12e0 -> 0x18fd12e0  (stayed put)
   16384 ints: 0x18fd12e0 -> 0xffff9310f010
```

I expected the block to move every time it grew. It stayed put eleven
times out of thirteen, because nothing had been allocated after it and
the **HEAP** could just stretch. It moved at 8 `int`s, and that one took
me a minute. Something had landed right behind my block. It was the
buffer `printf()` allocates for stdout the first time you call it, and
when I turned buffering off with `setvbuf()`, the block stayed put at 8
too. Then at 16384 `int`s, the doubling asked for 128 KiB and the
address jumped from `0x18fd12e0` up to `0xffff9310f010`, a long way from
the **HEAP** and out in the memory-mapped region from the map.

You can't count on staying put. If anything else holds a pointer into
the old block, a move leaves it pointing at memory that has been
returned. We'll spend some time on that in [pointer
pitfalls][pointer-pitfalls].

One more thing about `realloc()`: handed **NULL**, it behaves exactly
like `malloc()`. That turns out to be convenient, as you'll see in the
last program.

## Where the Bytes Come From

The last article ended with a challenge: `malloc()` a megabyte and see
whether the address looks like the **HEAP** or like the memory-mapped
regions. Here is my answer. This program allocates four blocks of
different sizes, prints where they landed, and then prints the range of
the `[heap]` mapping from `/proc/self/maps`:

```C
/* source.c - where do blocks of different sizes come from? */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    size_t sizes[] = { 100, 100000, 200000, 1000000 };
    char line[256];
    FILE *maps = fopen("/proc/self/maps", "r");

    for (size_t i = 0; i < sizeof(sizes) / sizeof(sizes[0]); i++) {
        printf("malloc(%7zu) -> %p\n", sizes[i], malloc(sizes[i]));
    }

    while (maps && fgets(line, sizeof(line), maps)) {
        if (strstr(line, "[heap]") != (char *)NULL) {
            printf("[heap] is %.17s\n", line);
        }
    }
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o source source.c
$ ./source
malloc(    100) -> 0x5122480
malloc( 100000) -> 0x5123500
malloc( 200000) -> 0xffff7fa5f010
malloc(1000000) -> 0xffff7f96a010
[heap] is 05122000-05143000
```

The first two blocks sit inside the `[heap]` range. The last two are far
away, up in the memory-mapped region. By default glibc serves requests
under 128 KiB from the **HEAP**, and anything bigger gets a mapping of
its own through `mmap()`. A block with its own mapping can be handed
straight back to the kernel when you free it. The 128 KiB threshold is
glibc's default, documented in [mallopt(3)][mallopt], and glibc adjusts
it as the program runs. Other allocators draw the line somewhere else.

That also explains the jump in `grow`. Doubling from 16384 to 32768
`int`s crossed the line.

## What You Asked For and What You Got

You'll also get more than you asked for, because the allocator rounds
every request up. On glibc you can ask what a block really holds with
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
        void *block = malloc(asked[i]);

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

Some of these have fine print. The function `reallocarray()` is what you
want when you're growing an array, since it gives `realloc()` the
overflow check that `calloc()` has. It isn't part of the C standard, but
glibc and the BSDs have it. The function `aligned_alloc()` arrived in
C11 for hardware that wants data on particular boundaries, such as
vector instructions. The function `strdup()` is POSIX and joined the C
standard in C23. It allocates room for the string and its terminator,
copies it, and hands you the result. You free it like anything else.

There is also `alloca()`, which allocates on the **STACK** and releases
the memory when the function returns, with no `free()`. It's quick, and
it tells you nothing when you've asked for too much. You find out when
the **STACK** limit from the last article does its thing. It isn't
standard either. I don't use it, and I'd rather you didn't.

## Putting It Together

Here is a program that uses almost all of it. It reads lines from
standard input into an array that grows as needed, then prints them in
reverse:

```C
/* lines.c - read lines from stdin, print them in reverse */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 256

typedef struct {
    char **items;
    size_t used;
    size_t capacity;
} list_t;

int list_add(list_t *list, const char *text) {
    if (list->used == list->capacity) {
        size_t capacity = (list->capacity == 0) ? 4 : list->capacity * 2;
        char **items = realloc(list->items, capacity * sizeof(*items));

        if (items == (char **)NULL) {
            return EXIT_FAILURE;
        }
        list->items = items;
        list->capacity = capacity;
    }

    list->items[list->used] = strdup(text);
    if (list->items[list->used] == (char *)NULL) {
        return EXIT_FAILURE;
    }
    list->used++;
    return EXIT_SUCCESS;
}

void list_free(list_t *list) {
    for (size_t i = 0; i < list->used; i++) {
        free(list->items[i]);
    }
    free(list->items);
}

int main(void) {
    list_t list = { (char **)NULL, 0, 0 };
    char buffer[BUFFER_SIZE];

    while (fgets(buffer, sizeof(buffer), stdin) != (char *)NULL) {
        buffer[strcspn(buffer, "\n")] = '\0';
        if (list_add(&list, buffer) != EXIT_SUCCESS) {
            fprintf(stderr, "out of memory\n");
            list_free(&list);
            return EXIT_FAILURE;
        }
    }

    for (size_t i = list.used; i > 0; i--) {
        printf("%s\n", list.items[i - 1]);
    }

    list_free(&list);
    return EXIT_SUCCESS;
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

- `list_add()` grows the array by doubling, through a temporary
pointer, so a failure never loses the old block
- the first call passes **NULL** to `realloc()`, which acts like
`malloc()`, so the empty list needs no special case
- `strdup()` copies each line onto the **HEAP**, which frees up
`buffer` to be reused for the next one
- `list_free()` frees each string before it frees the array, because
the array holds the only pointers to those strings

I also built it once with `-fsanitize=address`, a gcc option that
catches leaks and bad memory accesses, and it had nothing to say. That
option gets a proper introduction in [pointer
pitfalls][pointer-pitfalls].

## Where To Go From Here

Take `lines.c` and break it three ways. Take out the `free()` of the
strings in `list_free()`. Swap the order so the array goes first. Then
write the `realloc()` line the way I told you not to. Before you run
each one, predict what will happen.

Then write something of your own that allocates, and count the
`malloc()`s and the `free()`s. When the two numbers disagree, you have a
leak. What happens when they disagree in other ways is the subject of
the next article.

Go borrow some memory, and give it back.

<!-- Links -->
[address-space]: ../address-space/article.md
[pointer-pitfalls]: ../pointer-pitfalls/article.md
[mallopt]: https://man7.org/linux/man-pages/man3/mallopt.3.html
