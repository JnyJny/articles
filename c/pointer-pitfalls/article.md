# Pointers II: Everything Is On Fire And It's Probably Your Fault

<!-- Prerequisite: ../pointers/article.md -->

You read the [pointers article][pointers]. You wrote some code. Things
broke. Welcome to the second lesson.

The first article was about how pointers work. This one is about how
they fail -- and more importantly, how to recognize the failure modes
before they recognize you.

## TODO: Outline

### The Lifecycle: malloc, use, free

- Heap vs stack allocation
- `malloc()` and `free()` -- the contract
- What "ownership" means when there's no garbage collector

### Dangling Pointers

- Returning a pointer to a local variable
- Use-after-free
- The insidious part: it often works until it doesn't

### Double Free

- Why freeing the same memory twice corrupts the heap
- How to defend against it (NULL after free)

### The sizeof Trap

- `sizeof(array)` vs `sizeof(pointer)` -- array decay strikes again
- Why your function that takes `int arr[]` doesn't know how big the array is
- The pattern: always pass the length separately

### Pointer-to-Pointer

- When you need to modify a caller's pointer (not just the data it points to)
- `char **argv` demystified
- Allocating inside a function and handing it back

### Buffer Overflows

- Walking off the end of an array, revisited with consequences
- Stack smashing and why the compiler warns you about `gets()`
- Bounds checking as a habit, not an afterthought

### Common Patterns for Staying Alive

- Always initialize pointers (NULL or valid address)
- NULL after free
- Validate at function boundaries
- Const-correctness as self-documentation
- Valgrind / AddressSanitizer as safety nets

## Where To Go From Here

<!-- Link to future articles: function pointers, opaque types, etc. -->

<!-- Links -->
[pointers]: ../pointers/article.md
