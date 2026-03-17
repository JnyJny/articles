# Article Style Guide

Ground rules for writing articles in this repo. Extracted from
existing published and in-progress work. When in doubt, read the
pointers and how-i-write-main articles -- they're the current gold
standard for tone and structure.

## Voice

- **First person, conversational, opinionated.** You're a working
  programmer talking to someone earlier in their journey. Not a
  textbook, not a blog-factory SEO piece.

- **Establish the relationship up front.** The Me/You intro block
  sets expectations:

  ```
  **Me**: a crusty Unix system programmer who has...
  **You**: someone who knows a little C and...
  ```

  Adapt the specifics to the article. Keep the format.

- **Have opinions and state them.** "I do this" is better than
  "one approach is." If there's a religious war (asterisk placement,
  tabs vs spaces), pick a side, explain why, and move on.

- **Humor is welcome, never forced.** Dry, self-deprecating, or
  observational. No memes, no "let's goooo," no emoji. If a joke
  doesn't land on paper, cut it.

- **Don't talk down.** The reader is smart but hasn't learned this
  yet. There's a difference. Never say "simply" or "obviously" about
  something you're taking the time to explain.

## Structure

- **One article per directory.** Each topic gets its own folder under
  the appropriate category (`c/`, `unix/`, `python/`, `misc/`). The
  main file is always `article.md`.

- **H1 title is the article title.** One per file. Make it
  memorable -- "How To Write a Good C Program, Like Me" over
  "Introduction to C Main Functions."

- **H2 for major sections.** Each section should teach one concept
  or build one layer on the previous section.

- **H3 sparingly.** For subsections within a concept (e.g.,
  individual operators under "The Two Operators You Need"). Don't
  nest deeper than H3.

- **Progressive disclosure.** Start simple, build complexity.
  Each section should be understandable given only the sections
  before it. Don't forward-reference concepts you haven't introduced
  yet without acknowledging the gap ("we'll get to that").

- **End with action.** The closing section should tell the reader
  to go write code, not summarize what they just read. They were
  there. They know.

## Code

- **All code examples must compile and run.** If you show it, it
  works. No pseudocode disguised as C. Partial snippets are fine
  when building up a concept, but the "putting it together" example
  must be complete and correct.

- **Use `gcc` for compilation examples.** It's what most readers
  will have.

  ```console
  $ gcc -o points points.c -lm
  $ ./points
  ```

- **Show the output.** After a complete runnable example, show what
  it prints. The reader should be able to verify they got the same
  result.

- **C style:**
  - Asterisk binds to variable name: `int *p`, not `int* p`
  - NULL is explicitly cast: `(int *)NULL`
  - Typedefs end with `_t`: `options_t`, `point_t`
  - Constants and macros in ALL_CAPS
  - Block comments use `/* */`, not `//`
  - EXIT_SUCCESS and EXIT_FAILURE, not 0 and -1

- **Comments in code examples should explain what the reader needs
  to see**, not narrate every line. Use them to highlight the
  teaching point:

  ```C
  int *p = &x;    /* p now holds the address of x */
  ```

## Diagrams

- **ASCII box diagrams for memory layout.** Use the established
  format:

  ```
      Variable    Address    Value
      ┌────────┬──────────┬────────┐
      │ int x  │  0x4004  │     42 │
      └────────┴──────────┴────────┘
  ```

- **Use Unicode box-drawing characters** (┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘ │ ─),
  not ASCII approximations.

- **Pointer arrows use dashed lines:** `─ ─ ┐` / `◄─ ─ ┘` /
  `─ ─ ▸`

- **Declaration order matters.** If x is declared before p, x
  appears above p in the diagram. Top-to-bottom should match the
  reader's mental model of what happened first.

## Links

- **Cross-reference other articles in the series.** Use relative
  paths: `../how-i-write-main/article.md`. This builds the web of
  knowledge and gives readers a trail to follow.

- **Future article links are placeholders.** Use descriptive slugs
  (`XX-my-time-among-the-linker-aliens`, `signals-and-segfaults`)
  that make the intended topic obvious. These are commitments to
  write, not decoration.

- **External links go to authoritative sources.** Wikipedia for
  concepts and history, man7.org for man pages, cppreference for
  C standard library details.

- **Link references go at the bottom of the file** in a comment-
  delimited block:

  ```markdown
  <!-- Links -->
  [segfault]: signals-and-segfaults
  [hoare]: https://en.wikipedia.org/wiki/Tony_Hoare
  ```

## Formatting

- **Bold for dangerous or important terms** everywhere they appear
  in prose (not just first mention). **NULL** is the prime example --
  it's special, it's dangerous, and it should look the part every
  time. Other key terms can use bold at first appearance and inline
  code thereafter.

- **Italics for definitions and conceptual emphasis:** _dereferencing_,
  _decays_ to a pointer.

- **Inline code for identifiers:** `main()`, `argv`, `sizeof(int)`.
  Anything that would appear in source code gets backticks.

- **Articles (a/an) before code identifiers** follow the spoken
  pronunciation. Python's dunder names use "a" not "an" because
  we say "dunder": a `__init__.py`, a `__main__.py`. For C
  identifiers, go by how you'd say it: an `int`, a `char *`.

- **Bulleted lists are fine** when you're dissecting something
  mechanical (function parameters, a checklist of what a program
  does). Use prose for narrative explanation. The format should
  match the information type.

- **Tables for structured reference data** (include files and what
  they provide, argument descriptions). Not for narrative content.

- **No markdown in code blocks.** Code is code.

## Naming

- **Article directory names are kebab-case:** `how-i-write-main`,
  `pointer-pitfalls`, `working-with-files`.

- **Article titles can be playful.** The directory name is for
  filesystems; the H1 title is for humans.

## Metadata

- **HTML comment block at the top of every article.** Invisible
  to readers, useful to us.

  ```markdown
  <!--
  Author: Erik O'Shaughnessy
  Editor: Johnny (Jny)
  Date: March 2026
  Status: draft | review | published
  Series: C Programming
  Prerequisites: how-i-write-main
  Next: pointer-pitfalls
  -->
  ```

- **Date** is when written or last substantially revised, not
  every typo fix.
- **Status** tracks where the article is in the pipeline.
- **Prerequisites** and **Next** make the reading order explicit
  without relying on scattered in-text cross-references.
- See `SKELETON.md` for the full article template.

## Audience

The reader knows what programming is. Maybe they've written Python
or JavaScript or even BASIC -- they understand variables, functions,
loops. They may have read K&R or they may not have, but either way
they're past "what is C" and into "how do I use C to get things
done." There are plenty of texts about what C is. These articles
are about wielding it.

Don't assume C literacy. Don't assume systems literacy (memory
addresses, the stack, how linking works). Do assume programming
literacy and the ability to follow a code example. Write for the
person who will actually type in your examples and run them.

## The Test

Before calling an article done, ask:

1. Does every code example compile and produce the shown output?
2. Would I have wanted to read this when I was learning?
3. Does the reader know what to do next?

If yes to all three, ship it.

## Pre-Push Checklist (Johnny)

Before pushing any article changes to GitHub:

1. Run a style guide pass on touched articles
2. Check heading levels (H1 for title, H2 for sections, H3 for subsections)
3. Verify code examples are complete and correct
4. Confirm link references at bottom are present and accounted for
5. Spell-check (typos happen to the best of us)
