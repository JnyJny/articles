# TODO

Ideas and loose ends that don't belong in the article being written.

## Housekeeping

- Sweep the articles for binary-prefix units (`KiB`, `MiB`, `GiB`, `TiB`)
  and write them as `KB`, `MB`, `GB`, `TB`, which is how Erik writes
  1024-based sizes. Checked 2026-11-13: only the address space article
  had any, and those are fixed on `main`. Run the grep again when new
  articles land.
- Sweep the older articles for link text. The rule (2026-11-14): link a
  phrase that belongs in the sentence, in lowercase, with a capital only
  at the start of a sentence, and never the full playful title. The new
  articles `memory-allocation` and `memory-allocation-brk` are done. Left
  to check: `address-space` (already lowercase, so probably fine),
  `pointers` (one title-cased link, `[How I Write Main]`), and the rest.
- Dangling links, 2026-11-15: every placeholder slug in the older
  articles now points at a real stub or at an existing article. Nine new
  stubs were created: `c/data-types`, `c/structures-unions-enumerations`,
  `c/mutable-vs-immutable`, `c/terse-c`, `c/goto`, `c/linker-aliens`,
  `c/virtual-memory`, `unix/signals` and `unix/traditions`. Each records
  the sentence that promised it, in a comment. Guesses worth checking:
  - `signals-and-segfaults` and `oh-boy-this-is-a-doozie` were two
    placeholders and now share `unix/signals`. Split if they outgrow one
    article.
  - The two "stack frame" and "stack" links (placeholder "names and
    spaces") now go to `address-space`. The `namespaces` stub (symbol
    tables, name to address) is no longer linked from anywhere.
  - "NULL pointer" in `how-i-write-main` links to the NULL section of
    `pointers` instead of getting its own stub.
  - `[cpp-for-newbs]` links to `compiler-tool-chain#cpp`, a section that
    doesn't exist yet. Link checks only test the file, not the anchor.
  - `[4]: Down to Program` in `packaging-with-poetry` ("be DtP") is the
    one dangler left. It is not an article, so no stub. Erik: what was it?
- Style sweep of the older articles, 2026-11-15, and what is left:
  - The metadata blocks added to the eight older articles are best
    guesses. The dates are the month each file first landed in this repo
    and may not be when it was written. Correct them as you remember.
    `Status: stub` is now an allowed value.
  - Leave "modern" as is, including the title of the command-line
    interface article. Erik may revisit it. Erik will revisit "honest" in
    `how-i-write-main` and `multi-file-c-program`, and "simply" in
    `yield`.
  - `multi-file-c-program` has no H1 title and uses H3 for every section.
    It needs a title (the README calls it "Multi-File C Programs") and
    its sections promoted to H2. Erik's call.
  - `learning-c` now has a README row marked Planned. Nothing is written.
  - Return codes should be `EXIT_SUCCESS` and `EXIT_FAILURE`, not bare
    integers. Done in `multi-file-c-program`. `compare_points()` in
    `pointers` returns -1, 0 or 1 because `qsort()` expects that.
- Four pointer-arrow diagrams in the `pointers` article have the elbows
  one column apart (around lines 114/117, 160/163, 239/243 and 335/340).
  The fix is the aligned pattern in `STYLE.md`: `─ ─ ─┐` over
  `◄─ ──┘`. Erik hasn't said yes yet. Render the page afterward.

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
- Restructured 2026-11-14: the `brk()` and `sbrk()` material moved to its
  own article, `c/memory-allocation-brk/`. `memory-allocation` now opens
  by saying it covers glibc's allocator, goes `malloc()` then `calloc()`,
  and has a "Type Them In" section. `realloc()` is only mentioned in the
  family table, on purpose: Erik almost never uses it. `lines.c` became
  a linked list so the article needs nothing but `malloc()`, `strdup()`
  and `free()`.
- Pointers in Erik's rewrite of `memory-allocation` (2026-11-14):
  - `[future-libc-article]` is "the C library". It points at the stub
    `c/standard-library/article.md`, which is where the libc discussion
    (glibc, musl, the BSDs) belongs. Erik's call, 2026-11-14.
  - `[link-to-glibc-docs]` points at the GNU C Library manual,
    https://www.gnu.org/software/libc/manual/. Check it's the page Erik
    wants.
  - There is deliberately no pointer for `sizeof`. Erik wants links to be
    big chunks for the reader to chew on. A reader who wonders what
    `sizeof` is can search for it, and raising the question is enough.
- Overcommit: on Linux `malloc()` rarely returns **NULL** for plausible
  sizes, because the kernel promises memory it hasn't got and the failure
  shows up later (the OOM killer). Left out of the article on purpose; it
  belongs with virtual memory.
- glibc internals behind what the article shows: chunk headers, the
  24-byte minimum block, the 16 bytes scribbled on a freed block, arenas,
  `brk()` versus `mmap()`. Candidate for an article of its own.
- `memory-allocation-brk` could grow: `bump()` with a `bump_free()` that
  only frees the last block, a free-list allocator in 50 lines that
  reuses holes, and a look at where glibc's numbers come from. Erik's
  idea: the simplest and oldest allocators help a person evaluate modern
  ones.

## Pointer pitfalls

- The memory allocation article promises a proper introduction to
  `-fsanitize=address` here. The `realloc()` leak trap (`p = realloc(p,
  n)` loses `p` on failure) and pointers into a block that outlive a
  `realloc()` that moved it no longer have a home in that article, since
  it skips `realloc()`. They fit here.
- Good opener for the AddressSanitizer introduction: run `overflow.c`
  from the memory allocation article with `-fsanitize=address`. It
  aborts with "calloc parameters overflow: count * size
  (4611686018427387904 * 4) cannot be represented in type size_t"
  instead of letting `calloc()` return NULL. Verified on gcc 14, aarch64
  Linux.
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

## Unix names

- Seed from the memory allocation article's `brk()` opener: an article on
  how Unix names got formed. Erik's version of the rules: drop the
  vowels, shorten what's left, and when all else fails use the initials
  of whoever wrote it. `brk` is _break_ with the vowel gone. More
  examples to collect (`creat`, `ls`, `cp`, `grep`, and the stories
  behind them). Let it grow; no rush. Erik likes the line "a
  three-letter incantation" and may want it back here.

## Integers

- Seed from the memory allocation article, where `count * sizeof(int)`
  wraps around to zero: an article on how integers are stored and how
  they misbehave. Two's complement, wraparound, shifts, rounding, and
  the difference between signed and unsigned overflow.
- `sizeof` goes with this note, as a piece of a discussion of C data
  types where `sizeof` is incidental. Erik's call, 2026-11-14. Things
  that discussion could cover: `sizeof` is an operator evaluated at
  compile time, not a function; it takes a type or an expression, which
  is why `sizeof(*p)` works with `p` unset; its result is a `size_t`;
  arrays decay to pointers and lose their size; padding in structures.
  No link from `memory-allocation`.

## Virtual memory

- The article is promised by the [address space][address-space]
  introduction, which links to `../virtual-memory/article.md`. The
  README has no row for it yet.
- Physical pages of read-only code can be shared between processes. This
  was cut from the address space article because it needs virtual memory
  first.

<!-- Links -->
[address-space]: c/address-space/article.md
