# TODO

Ideas and loose ends that don't belong in the article being written.

## Address space

- Preface the whole article: we are talking about one specific version of
  Linux (gcc 14, aarch64, non-PIE), and working out the specifics of your
  own operating system is up to you. Currently only the Mac and Windows
  asides gesture at this.
- Story seed for the **TEXT** section ("I can't believe we got away with
  that!"): Erik's branch tracing framework on SPARC. It replaced branch
  instructions (control transfer instructions, CTIs) with `ILLTRAP`, and
  the `ILLTRAP` trap handler emitted a trace record, emulated the branch,
  and returned control to wherever the CTI was supposed to go. Needs
  writable text. Erik says he abused the stack more than the gap. Re-read
  the old framework for the details first (delay slots? where the handler
  ran?).
- Second story seed, probably not **TEXT**: Erik wrote Python that modified
  itself to do something dumb, while trying to monitor CPU throttling due
  to temperature on Solaris. Details lost; ask Erik. May fit a different
  article.
- Third story seed: Erik patched a running kernel to fix a performance
  problem in a counter collection subsystem. "Dicey but it worked."
  Solaris on SPARC. Other details unknown; ask Erik. (Erik did fewer
  bad things to AIX and POWER, being less confident then.)
- Idea: a `misc/` article collecting these ("I can't believe we got away
  with that!"), with the address space article carrying a one-line
  teaser.

## Memory allocation

- Drafted 2026-11-13 on `features/memory-allocation-article`, waiting for
  Erik's edit pass.
- Overcommit: on Linux `malloc()` rarely returns **NULL** for plausible
  sizes, because the kernel promises memory it hasn't got and the failure
  shows up later (the OOM killer). Left out of the article on purpose; it
  belongs with virtual memory.
- glibc internals behind what the article shows: chunk headers, the
  24-byte minimum block, the 16 bytes scribbled on a freed block, arenas,
  `brk()` versus `mmap()`. Candidate for an article of its own.

## Pointer pitfalls

- The memory allocation article promises two things here: a proper
  introduction to `-fsanitize=address`, and what goes wrong when pointers
  into a block outlive a `realloc()` that moved it.
- `char *greeting = "hello";` and `char greeting[] = "hello";` look
  alike and behave differently. The pointer refers to read-only
  characters in `.rodata`, and writing through it segfaults. The array
  is a writable copy on the stack. Verified on Linux: the pointer
  variable lives on the stack and holds an address in `.rodata`, which
  shares the read-only, executable mapping with `.text`. Held back from
  the [address space][address-space] article so the reader has the whole
  map first.

## Linker aliens

- In a non-PIE executable, `(void *)printf` is the address of the PLT
  stub in the executable (`0x4005e0` in one run), not the address of
  `printf()` in libc. Found while writing the address space article.

## Virtual memory

- The article is promised by the [address space][address-space]
  introduction, which links to `../virtual-memory/article.md`. The
  README has no row for it yet.
- Physical pages of read-only code can be shared between processes. This
  was cut from the address space article because it needs virtual memory
  first.

<!-- Links -->
[address-space]: c/address-space/article.md
