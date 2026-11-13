<!--
Author: Erik O'Shaughnessy
Editor: Johnny (Jny)
Date: November 2026
Status: draft
Series: C Programming
Prerequisites: pointers
Next: memory-allocation
-->

# A Map of Memory: The Process Address Space

The first time I got a segfault, I assumed the computer was broken. The
second time, I assumed I was. By the tenth I had figured out that the
computer had a map, I didn't, and it was enforcing the borders anyway.

**Me**: an old Unix hand who navigated by core dump before debuggers
had colors.

**You**: someone who knows what a pointer is and wants to know what
it's pointing _into_.

Let's draw the map.

## The Big Picture

People say "memory" as if it were one enormous array of bytes. What
your program actually gets is a _virtual address space_: a private
range of addresses that the operating system builds for your process
and that no other process can see. Your `0x4004` and another
process's `0x4004` are different bytes in different places, and
neither of you can tell. How does that work? It's a [sacred
mystery][virtual-memory], the next rung on the ladder from C
programmer to operating system wizard. Master the map first and the
wizards will let you in.

The kernel carves that space into regions. Each region has a purpose
and a set of permissions that answer three questions: can you read
here, write here, execute code here? Here is the layout on Linux,
which is where every example in this article was run:

```
    High addresses
    ┌─────────────────────────────┐
    │            STACK            │  ← grows downward
    │              ↓              │
    ├─────────────────────────────┤
    │       (unmapped gap)        │
    ├─────────────────────────────┤
    │   Memory-mapped regions     │  ← shared libraries, mmap()
    ├─────────────────────────────┤
    │       (unmapped gap)        │
    ├─────────────────────────────┤
    │              ↑              │
    │            HEAP             │  ← grows upward
    ├─────────────────────────────┤
    │             BSS             │  ← uninitialized globals
    ├─────────────────────────────┤
    │            DATA             │  ← initialized globals
    ├─────────────────────────────┤
    │            TEXT             │  ← your compiled code
    ├─────────────────────────────┤
    │         (reserved)          │  ← NULL lives here
    └─────────────────────────────┘
    Low addresses
```

Every region has rules and a way to get you in trouble. We'll walk
the map from the bottom up.

If you're on a Mac, the same regions exist but the neighborhood is
arranged differently, and there is no `/proc` to ask. I ran
everything here in a Linux container. Any Linux box will show you the
same thing, with different numbers.

In the spirit of magnanimity, Windows has an address space too. I'm
told it is divided into segments for bugs, hacks, hacked bugs,
exploits, terrible code, and Clippy. Someone braver than me can draw
that map.

## Text: Where Your Code Lives

When you compile a program, the compiler produces machine
instructions. When you run it, the kernel maps those instructions into
the bottom of your address space as the **TEXT** region and marks it
_read-only and executable_. Your own program should not change its
code while it runs, and the hardware will object if it tries. You can
talk the system into allowing it, and the stories that follow tend to
end with "I can't believe we got away with that!"

Code that never changes has a pleasant side effect, but it's one for
the [virtual memory][virtual-memory] article.

String literals tend to end up in read-only memory close to the code,
which explains a crash that has ambushed many a beginner:

```C
char *greeting = "hello";
greeting[0] = 'j';    /* segfault: this memory is read-only */
```

The compiler let you do it. The map did not.

## Data: Initialized Globals

Just above the code sits **DATA**: global and `static` variables that
were given a value in the source.

```C
int initialized_global = 42;
```

The 42 is written into the executable file itself, and the kernel
loads it into memory, writable, before `main()` starts. The variable
lives until the process exits. Every function in the program can see
it, which is why globals are tempting and why they get expensive later.

A `static` variable declared inside a function is stored here too. Its
name has local scope, but its storage has program lifetime. Call the
function a thousand times and it remembers.

## BSS: The Zeroed Wasteland

Next comes **BSS**, home of globals and statics that were _not_ given a
value:

```C
int uninitialized_global;
```

C guarantees these start out as zero. You will never find leftover
garbage in a global, which makes them the one place in C where
uninitialized means something specific.

Why a separate region, when **DATA** would do? Because zeros are cheap.
The executable file doesn't need to contain a million zeros to
describe a million-int array. It only needs to say "a million ints,
please" and the kernel hands over pages of zeros at load time. Compare
two programs that differ only in whether the array has an initializer:

```C
int table[1000000];         /* bss.c  */
int table[1000000] = {1};   /* data.c */
```

Each has a trivial `main()` that returns `table[0]`. Compile both and
look at the files:

```console
$ ls -l bss data
-rwxr-xr-x. 1 root root   70368 Nov 13 00:40 bss
-rwxr-xr-x. 1 root root 4070368 Nov 13 00:40 data
$ size bss data
   text	   data	    bss	    dec	    hex	filename
   1225	    576	4000008	4001809	 3d1011	bss
   1225	4000576	      8	4001809	 3d1011	data
```

Same array, same four megabytes at runtime, and a 4 MB difference on
disk. The name comes from a 1950s assembler directive, "Block Started
by Symbol," and nobody has had enough reason to rename it in seventy
years. Wikipedia has the [history][bss].

One honest caveat: the kernel doesn't distinguish **DATA** from **BSS** at
runtime. Both end up in a single read-write mapping, as you'll see in
a few pages. The split exists in the file.

## Heap: The Wild West

Above **BSS** is the **HEAP**, the region that `malloc()` carves up. It is
the first region whose size you control while the program runs, and
the first where nobody cleans up after you.

When `malloc()` runs short of space, it asks the kernel to move the
upper edge of the **HEAP** (the _program break_) upward. That's the arrow
in the diagram: the **HEAP** grows toward higher addresses. When you call
`free()`, the allocator takes the block back for reuse. The **HEAP** is a
pool the allocator manages on your behalf, and you are responsible for
giving every block back.

"Dynamic" allocation means the size and lifetime of the memory are
decided while the program runs. The compiler has no say. That freedom
is why linked lists and growable buffers are
possible, and it is also why leaks, double frees, and use-after-free
exist. The next article, [memory allocation][memory-allocation], takes
the **HEAP** apart. For now, notice where it lives.

## Stack: The Call Stack

At the top of the map is the **STACK**. Every time a function is
called, a _frame_ is pushed holding the function's local variables, its
arguments, and the address to return to. When the function returns,
the frame is popped. This is where `int local = 7;` lives, and it's
why locals are fast and why they disappear.

The **STACK** grows _downward_, from high addresses toward low ones, and it
has a fixed size limit. You can ask your shell what yours is:

```console
$ ulimit -s
8192
```

That's 8192 KiB, eight megabytes. We can use up eight megabytes
quickly with a function that calls itself forever:

```C
/* recurse.c - find out how deep the stack goes */
#include <stdio.h>
#include <stdlib.h>

void descend(int depth) {
    char frame[1024];

    frame[0] = (char)depth;
    if (depth % 1000 == 0) {
        fprintf(stderr, "depth %d, frame at %p\n", depth, (void *)frame);
    }
    descend(depth + 1);
    frame[1] = frame[0];    /* keeps the compiler from turning this into a loop */
}

int main(void) {
    descend(1);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o recurse recurse.c
recurse.c: In function 'descend':
recurse.c:5:6: warning: infinite recursion detected [-Winfinite-recursion]
    5 | void descend(int depth) {
      |      ^~~~~~~
recurse.c:12:5: note: recursive call
   12 |     descend(depth + 1);
      |     ^~~~~~~~~~~~~~~~~
$ ./recurse
depth 1000, frame at 0xffffe545cf30
depth 2000, frame at 0xffffe535b230
depth 3000, frame at 0xffffe5259530
depth 4000, frame at 0xffffe5157830
depth 5000, frame at 0xffffe5055b30
depth 6000, frame at 0xffffe4f53e30
depth 7000, frame at 0xffffe4e52130
Segmentation fault (core dumped)
```

Watch the addresses. Each thousand calls moves the frame down by about
a megabyte (1024 bytes of array plus a little overhead per call), and
somewhere before depth 8000 the **STACK** runs out. gcc saw this coming
and said so. Yes, this is where the website gets its name.

The **STACK** has one more trap, and it's the one that bites people who
are otherwise careful. Frames are temporary. A pointer to a local
variable points into a frame that stops existing the moment the
function returns:

```C
/* dangling.c - hand back a pointer to a local variable */
#include <stdio.h>
#include <stdlib.h>

int *answer(void) {
    int result = 42;

    return &result;
}

int main(void) {
    int *p = answer();

    printf("answer() gave us %p\n", (void *)p);
    printf("%d\n", *p);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o dangling dangling.c
dangling.c: In function 'answer':
dangling.c:8:12: warning: function returns address of local variable [-Wreturn-local-addr]
    8 |     return &result;
      |            ^~~~~~~
$ ./dangling
answer() gave us (nil)
Segmentation fault (core dumped)
```

I expected to read stale data out of a dead frame. Recent versions of
gcc are so sure this is a bug that they compile `answer()` to return
**NULL**. Compile with the warning on, read the
warning, and believe it. [Pointer pitfalls][pointer-pitfalls] has more
ways to hurt yourself in this neighborhood.

## The Gap

Between the **HEAP** and the **STACK** lies a vast stretch of address space
that nothing is mapped into. The map has no entry for it. Touch it and
the hardware raises a fault, the kernel finds no mapping, and your
process receives a `SIGSEGV`:

```C
/* gap.c - touch an address nobody mapped */
#include <stdlib.h>

int main(void) {
    int *in_the_gap = (int *)0x10000000;

    *in_the_gap = 1;
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o gap gap.c
$ ./gap
Segmentation fault (core dumped)
```

That is all a segfault is: an access to an address that isn't mapped,
or mapped without the permission you asked for. Writing to the **TEXT**
region from a few sections ago fails for the second reason. Dereferencing
**NULL** fails for the first, because the lowest page of the address
space is deliberately left unmapped so that **NULL** dereferences get
caught.

The gap is also why your addresses are not mine. Every time a program
starts, the kernel picks a different location for the **STACK**, the **HEAP**,
and the memory-mapped regions. This is [address space layout
randomization][aslr] (ASLR), and it exists so that an attacker who
finds a bug can't rely on knowing where anything is. Three runs of the
same program:

```console
$ ./address_map | grep STACK
STACK  local variable         0xffffe8b42c54
STACK  local variable         0xfffff505bf74
STACK  local variable         0xffffc7cd7f14
```

Never hardcode an address, and never compare addresses printed by
different runs. On the Linux system I used, the **TEXT** region stays put
at `0x400000` because that binary was not built as a position-independent
executable. Most distributions build them by default, which randomizes
the code too.

## Memory-Mapped Regions

Out in the gap, scattered through the middle of the address space, are
regions that were created with `mmap()`. The `mmap()` system call asks
the kernel for new pages, optionally backed by a file. The program
loader uses it to bring in shared libraries, `malloc()` uses it for
large blocks, and you can use it to treat a file as if it were an
array.

Every program that calls `printf()` has libc mapped into this area.
You'll see libc in the output below, mapped four times with four
different permission sets.
It also shows the dynamic linker (`ld-linux`) that put it there and
a `[vdso]`, a page of code the kernel provides so that a few system
calls, like reading the clock, don't require a trip into the kernel.
How libraries get found and wired together is a story for the
[linker aliens][linker-aliens].

## Putting It Together

Here is a program that prints one address from each region, and then,
if you give it any argument, prints the kernel's own record of the
map from `/proc/self/maps`:

```C
/* address_map.c - print one address from each region of the map */
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>

int initialized_global = 42;    /* DATA */
int uninitialized_global;       /* BSS  */

void show(const char *region, const char *what, void *address) {
    printf("%-6s %-22s %p\n", region, what, address);
}

int main(int argc, char *argv[]) {
    int local = 7;
    int *heap_block = malloc(sizeof(*heap_block));
    void *mapped = mmap((void *)NULL, 4096, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

    show("TEXT", "main()", (void *)main);
    show("TEXT", "string literal", (void *)"hello");
    show("DATA", "initialized_global", &initialized_global);
    show("BSS", "uninitialized_global", &uninitialized_global);
    show("HEAP", "malloc(4) block", heap_block);
    show("MAP", "mmap() page", mapped);
    show("STACK", "local variable", &local);

    if (argc > 1) {
        /* the kernel's own account of the map, Linux only */
        char line[256];
        FILE *maps = fopen("/proc/self/maps", "r");

        while (maps && fgets(line, sizeof(line), maps)) {
            fputs(line, stdout);
        }
    }

    free(heap_block);
    return EXIT_SUCCESS;
}
```

```console
$ gcc -Wall -o address_map address_map.c
$ ./address_map maps
TEXT   main()                 0x40083c
TEXT   string literal         0x4009f0
DATA   initialized_global     0x420060
BSS    uninitialized_global   0x420074
HEAP   malloc(4) block        0x2644f2a0
MAP    mmap() page            0xffff8481f000
STACK  local variable         0xfffff027e654
00400000-00401000 r-xp 00000000 00:43 138531946    /tmp/address_map
0041f000-00420000 r--p 0000f000 00:43 138531946    /tmp/address_map
00420000-00421000 rw-p 00010000 00:43 138531946    /tmp/address_map
2644f000-26470000 rw-p 00000000 00:00 0            [heap]
ffff84620000-ffff847bc000 r-xp 00000000 00:43 130049501  .../libc.so.6
ffff847bc000-ffff847cd000 ---p 0019c000 00:43 130049501  .../libc.so.6
ffff847cd000-ffff847d0000 r--p 0019d000 00:43 130049501  .../libc.so.6
ffff847d0000-ffff847d2000 rw-p 001a0000 00:43 130049501  .../libc.so.6
ffff847d2000-ffff847df000 rw-p 00000000 00:00 0
ffff847e8000-ffff84810000 r-xp 00000000 00:43 130049481  .../ld-linux-aarch64.so.1
ffff84817000-ffff84819000 rw-p 00000000 00:00 0
ffff8481f000-ffff84822000 rw-p 00000000 00:00 0
ffff84822000-ffff84824000 r--p 00000000 00:00 0    [vvar]
ffff84824000-ffff84826000 r-xp 00000000 00:00 0    [vdso]
ffff84826000-ffff84828000 r--p 0002e000 00:43 130049481  .../ld-linux-aarch64.so.1
ffff84828000-ffff84829000 rw-p 00000000 00:00 0
fffff025e000-fffff027f000 rw-p 00000000 00:00 0    [stack]
```

I shortened the library paths and the spacing in the listing to fit
the page. The `r-xp` and `rw-p` columns are the permissions: read,
write, execute, and private. Match each address from the first seven
lines against the ranges in the rest, and the map shows up:

```
    Region   Address          Found in /proc/self/maps
    ┌───────┬────────────────┬──────────────────────────────────────┐
    │ STACK │ 0xfffff027e654 │ fffff025e000-fffff027f000  [stack]   │
    ├───────┼────────────────┼──────────────────────────────────────┤
    │ MAP   │ 0xffff8481f000 │ ffff8481f000-ffff84822000  anonymous │
    ├───────┼────────────────┼──────────────────────────────────────┤
    │ HEAP  │ 0x2644f2a0     │ 2644f000-26470000          [heap]    │
    ├───────┼────────────────┼──────────────────────────────────────┤
    │ BSS   │ 0x420074       │ 00420000-00421000          rw-p      │
    │ DATA  │ 0x420060       │ (same mapping as BSS)                │
    ├───────┼────────────────┼──────────────────────────────────────┤
    │ TEXT  │ 0x40083c       │ 00400000-00401000          r-xp      │
    └───────┴────────────────┴──────────────────────────────────────┘
```

A few things to notice. The **HEAP** mapping is 132 KiB although we asked
for four bytes, because the allocator grabs a generous chunk from the
kernel and parcels it out, and asking the kernel is the expensive part.
The **DATA** and **BSS** variables sit twenty bytes apart in the same page, as
promised. And the **STACK**, the libraries, and our `mmap()` page are all
up near the top of the 48-bit address space, a long way from the **HEAP**,
with nothing but gap in between.

## Where To Go From Here

Run `address_map` on your own machine and compare it to mine. Then
break it. `malloc()` a megabyte and see whether the address looks like
the **HEAP** or like the memory-mapped regions. Declare a local array
bigger than the **STACK** limit and read the crash. Print a few more
addresses and predict which mapping each one will land in before you
look.

When you can name the region an address lives in, you can read a
segfault. When you're ready for the **HEAP** in detail, the next article
is [memory allocation][memory-allocation].

Go draw your own map.

<!-- Links -->
[pointers]: ../pointers/article.md
[virtual-memory]: ../virtual-memory/article.md
[memory-allocation]: ../memory-allocation/article.md
[pointer-pitfalls]: ../pointer-pitfalls/article.md
[linker-aliens]: XX-my-time-among-the-linker-aliens
[bss]: https://en.wikipedia.org/wiki/.bss
[aslr]: https://en.wikipedia.org/wiki/Address_space_layout_randomization
