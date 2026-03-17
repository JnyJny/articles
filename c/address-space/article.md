<!--
Author: Erik O'Shaughnessy
Editor: Johnny (Jny)
Date: March 2026
Status: draft
Series: C Programming
Prerequisites: pointers
Next: memory-allocation
-->

# A Map of Memory: The Process Address Space

People say "memory" like it's one place. It's not. It's a country
with provinces, borders, and rules about who's allowed where. If
you're going to write C, you need the map.

**Me**: a crusty Unix system programmer who has segfaulted in every
province and lived to tell about it.

**You**: someone who knows what a pointer is and wants to know what
it's pointing _into_.

Let's draw the map.

## The Big Picture

When your program runs, the operating system gives it a virtual
address space -- a private view of memory that belongs to your
process alone. It looks something like this:

```
    High addresses
    ┌──────────────────────┐
    │        Stack         │  ← grows downward
    │          ↓           │
    ├──────────────────────┤
    │                      │
    │    (unmapped gap)    │
    │                      │
    ├──────────────────────┤
    │          ↑           │
    │        Heap          │  ← grows upward
    ├──────────────────────┤
    │        BSS           │  ← uninitialized globals
    ├──────────────────────┤
    │        Data          │  ← initialized globals
    ├──────────────────────┤
    │        Text          │  ← your compiled code
    ├──────────────────────┤
    │     (reserved)       │  ← NULL lives here
    └──────────────────────┘
    Low addresses
```

Every one of these regions has a purpose, rules, and a way to get
you into trouble. Let's walk through them.

## Text: Where Your Code Lives

TODO: read-only, executable, shared between instances of the same
program, why you can't self-modify (easily), this is what the
compiler produces

## Data: Initialized Globals

TODO: global and static variables with explicit initial values,
read-write, lives for the entire program lifetime, the linker puts
it here

## BSS: The Zeroed Wasteland

TODO: uninitialized globals and statics, guaranteed zeroed at
program start, the name (Block Started by Symbol) and its history,
why it exists as a separate segment (saves space in the binary)

## Heap: The Wild West

TODO: where malloc() carves out space, grows upward toward the
stack, the allocator as land management, what "dynamic" allocation
really means, why you have to give it back (free), preview of the
memory allocation article

## Stack: The Call Stack

TODO: function call frames, local variables live here, grows
downward, finite size (ulimit -s), what happens when you blow it
(stack overflow), why returning a pointer to a local variable is
a death wish, recursion and stack depth

## The Gap

TODO: unmapped region between heap and stack, what happens when you
touch it (segfault), address space layout randomization (ASLR) and
why the map isn't the same every time

## Memory-Mapped Regions

TODO: shared libraries, mmap'd files, where they live in the gap,
the dynamic linker's playground (light touch -- linker aliens article
goes deeper)

## Putting It Together

TODO: a program that prints addresses of variables in each region,
showing the map is real and observable

```C
/* address_map.c */
/* TODO: complete example */
```

```console
$ gcc -o address_map address_map.c
$ ./address_map
```

## Where To Go From Here

Now you know the terrain. Next we'll talk about the heap in detail
-- how malloc() and free() work, what happens when you use them
wrong, and why memory allocation is the second biggest source of
bugs in C after off-by-one errors.

<!-- Links -->
[pointers]: ../pointers/article.md
[memory-allocation]: ../memory-allocation/article.md
[pointer-pitfalls]: ../pointer-pitfalls/article.md
