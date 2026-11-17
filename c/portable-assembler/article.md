<!--
Author: Erik O'Shaughnessy
Editor: Claude
Date: November 2026
Status: draft
Series: C Programming
Prerequisites: integers
Next: none
-->

# The Portable Assembler: How C Types Pick Instructions

C has long been called a portable assembler. The name is a little
unfair, since C is not assembly, and a little accurate. You write `a +
b` and the compiler decides which instruction to emit. The part that
earns the name is how it decides. The types of `a` and `b` choose the
instruction, and the types are written right there in your C. The same
source compiles for every CPU, and each compiler implementation has to
find the matching instructions for its own. In this article we're going
to compile some tiny functions for two different CPUs and read what
comes out.

**Me**: a crusty Unix system programmer who thinks of C as a portable
assembler.

**You**: someone who has met signed and unsigned integers, perhaps in
[the integers article][integers], and wants to see what the machine does
with the difference.

Let's read some assembly.

## Same Source, Different Types

In [the integers article][integers], the same eight bits could be 255 or
-1, and the type said which. That decision has to be made somewhere, and
the compiler makes it by picking different instructions. Here is a file
of tiny function pairs that differ only in their types:

```C
/* kinds.c - the same source with different types: compile it, don't run it */
#include <stdint.h>

int32_t add_signed(int32_t a, int32_t b)
{
    return a + b;
}

uint32_t add_unsigned(uint32_t a, uint32_t b)
{
    return a + b;
}

int32_t shift_signed(int32_t x)
{
    return x >> 2;
}

uint32_t shift_unsigned(uint32_t x)
{
    return x >> 2;
}

int32_t divide_signed(int32_t a, int32_t b)
{
    return a / b;
}

uint32_t divide_unsigned(uint32_t a, uint32_t b)
{
    return a / b;
}

int less_signed(int32_t a, int32_t b)
{
    return a < b;
}

int less_unsigned(uint32_t a, uint32_t b)
{
    return a < b;
}

int32_t load_int8(const int8_t *p)
{
    return *p;
}

int32_t load_uint8(const uint8_t *p)
{
    return *p;
}

int32_t load_char(const char *p)
{
    return *p;
}

void store_byte(uint8_t *p, int32_t value)
{
    *p = (uint8_t)value;
}
```

Compile it to assembly and look at the result. The `-S` flag stops the
compiler after the stage that writes assembly, one of the stopping
points in the [compiler tool chain][tool-chain], and `-O2` keeps the
output short. On x86-64 I also used `-masm=intel`, which puts the
destination first the way the aarch64 assembler does.

```console
$ gcc -O2 -S -o kinds.s kinds.c
$ grep -v '^\s*\.' kinds.s
```

Here are the instructions that matter, from gcc 14 on aarch64 and on
x86-64. Your registers and your compiler version may differ, but each
pair should differ the same way.

| The C | aarch64 | x86-64 |
|-------|---------|--------|
| `a + b`, signed | `add w0, w0, w1` | `lea eax, [rdi+rsi]` |
| `a + b`, unsigned | `add w0, w0, w1` | `lea eax, [rdi+rsi]` |
| `x >> 2`, signed | `asr w0, w0, 2` | `sar eax, 2` |
| `x >> 2`, unsigned | `lsr w0, w0, 2` | `shr eax, 2` |
| `a / b`, signed | `sdiv w0, w0, w1` | `idiv esi` |
| `a / b`, unsigned | `udiv w0, w0, w1` | `div esi` |
| `a < b`, signed | `cmp`, then `cset w0, lt` | `cmp`, then `setl al` |
| `a < b`, unsigned | `cmp`, then `cset w0, cc` | `cmp`, then `setb al` |
| load an `int8_t` | `ldrsb w0, [x0]` | `movsx eax, BYTE PTR [rdi]` |
| load a `uint8_t` | `ldrb w0, [x0]` | `movzx eax, BYTE PTR [rdi]` |
| load a `char` | `ldrb w0, [x0]` | `movsx eax, BYTE PTR [rdi]` |
| store a byte | `strb w1, [x0]` | `mov BYTE PTR [rdi], sil` |

## Reading the Pairs

Read the table a pair at a time. Addition is the one place where the
type makes no difference. Signed and unsigned `a + b` compile to the
same instruction, which is the economy of two's complement: one circuit
serves both readings. (gcc spells the addition `lea` on x86-64. Both
functions get the same one.)

Everything else splits. Right shifts get two instructions. The signed
shift is an _arithmetic_ shift, `asr` or `sar`, which copies the sign
bit into the vacated positions. The unsigned shift is a _logical_ shift,
`lsr` or `shr`, which brings in zeros. The integers article shows [what
that does to a negative number][integers-shifts]. Division gets two
instructions as well, and x86-64 has to prepare for each: a `cdq` that
sign-extends `eax` into `edx` before the signed `idiv`, and an `xor edx,
edx` that zeroes `edx` before the unsigned `div`.

Comparisons use the same `cmp` and test different conditions after it:
`lt` or `setl` for signed, and `cc` or `setb` for unsigned, which is how
the CPU spells "below". That's why `-1 < 1u` came out false in [the
integers article][integers-compare]. Once the -1 was converted to
unsigned, the compiler picked the unsigned condition, and `0xffffffff`
is not below 1.

The loads are where the `char` surprise comes from. `ldrsb` and `movsx`
_sign-extend_ a byte, copying its top bit up through the register, and
`ldrb` and `movzx` _zero-extend_ it. The byte `0xc8` becomes -56 when it
is loaded with one and 200 when it's loaded with the other. Look at the
`char` row. On aarch64, gcc loads a plain `char` with `ldrb`, so it's
unsigned. On x86-64, it uses `movsx`, so it's signed. The source code is
the same and the instruction is different.

The store at the bottom explains how 300 became 44 when it was stored in
an `unsigned char`. A byte store writes the low 8 bits of a register and
nothing else. Nothing in the program computes 300 modulo 256. The `strb`
instruction only has room for eight bits.

## Width Is a Species Too

Signedness is half of it. The other half is width. Here are four more
functions:

```C
/* widths.c - the same source with different widths */
#include <stdint.h>

int32_t add_int32(int32_t a, int32_t b)
{
    return a + b;
}

int64_t add_int64(int64_t a, int64_t b)
{
    return a + b;
}

int32_t load_int16(const int16_t *p)
{
    return *p;
}

int64_t load_int64(const int64_t *p)
{
    return *p;
}
```

| The C | aarch64 | x86-64 |
|-------|---------|--------|
| `a + b`, 32 bits | `add w0, w0, w1` | `lea eax, [rdi+rsi]` |
| `a + b`, 64 bits | `add x0, x0, x1` | `lea rax, [rdi+rsi]` |
| load an `int16_t` | `ldrsh w0, [x0]` | `movsx eax, WORD PTR [rdi]` |
| load an `int64_t` | `ldr x0, [x0]` | `mov rax, QWORD PTR [rdi]` |

The `w` registers on aarch64 are the narrow views of the wide `x`
registers, and `eax` is the narrow view of `rax` on x86-64. A 32-bit add
uses the narrow register and a 64-bit add uses the wide one. The loads
come in byte, halfword, word and doubleword forms, and the one that gets
used follows the type of the thing being loaded. Between signedness and
width, the declaration on a variable settles which instruction the
compiler picks.

## Portable, Within Reason

Look at the two columns together. Every place where the aarch64 column
has a pair of different instructions, the x86-64 column has a pair as
well. The names differ, the encodings differ and x86-64 needs a little
more setup, but the species are the same: a shift that copies the sign
bit and one that doesn't, a load that extends a byte with its sign and
one that doesn't. That is what portable means here. You write the same C
for both machines, the types carry the intent, and each compiler
implementation maps it onto the instructions its CPU has.

The portability has an edge, and the `char` row is where you find it.
The standard leaves the signedness of plain `char` to the
implementation, so the same source compiled for two machines means two
things. The program builds everywhere and means something different on
each. Undefined behavior is different again. The test in [the integers
article][integers-undefined] that asked whether `x + 1 < x` had no
instruction at all, because the compiler deleted it. When the C doesn't
say what should happen, a compiler may choose anything, and what it
chooses is not always an instruction.

## Where To Go From Here

Pick a function from your own code and compile it with `-S`. Change one
type, from `int32_t` to `uint32_t` or from `int32_t` to `int64_t`,
compile again and compare the two `.s` files with `diff`. Find the line
that changed, and say out loud what the CPU is now being asked to do. If
you can borrow a second kind of machine, or a cross-compiler, run the
same experiment there and see which of the differences travel with the
type.

<!-- Links -->
[integers]: ../integers/article.md
[integers-shifts]: ../integers/article.md#shifts
[integers-compare]: ../integers/article.md#when-signed-meets-unsigned
[integers-undefined]: ../integers/article.md#signed-overflow-is-undefined
[tool-chain]: ../compiler-tool-chain/article.md
