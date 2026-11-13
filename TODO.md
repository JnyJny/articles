# TODO

Ideas and loose ends that don't belong in the article being written.

## Address space

- Preface the whole article: we are talking about one specific version of
  Linux (gcc 14, aarch64, non-PIE), and working out the specifics of your
  own operating system is up to you. Currently only the Mac and Windows
  asides gesture at this.

## Pointer pitfalls

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
