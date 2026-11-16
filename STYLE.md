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

  Adapt the specifics to the article. The Me/You pairing is canon: say
  who you are and who the reader is, early. The labeled block is only
  one way to do it. Two sentences of prose that say the same thing
  work as well.

- **Have opinions and state them.** "I do this" is better than
  "one approach is." If there's a religious war (asterisk placement,
  tabs vs spaces), pick a side, explain why, and move on.

- **Humor is welcome, never forced.** Dry, self-deprecating, or
  observational. No memes, no "let's goooo," no emoji. If a joke
  doesn't land on paper, cut it.

- **Don't talk down.** The reader is smart but hasn't learned this
  yet. There's a difference. Never say "simply" or "obviously" about
  something you're taking the time to explain.

- **Say what "it" is.** A pronoun whose noun lives in an earlier
  sentence makes the reader go back and find it. Repeat the noun and
  spend the extra words: "Keep the pointer after the function returns",
  not "Keep it". When a sentence starts with "It", "This" or "That",
  make sure the noun is the last thing in the sentence before.

- **Pass on experience.** The reader can pick up knowledge in all sorts
  of ways, some harder and some easier. What they can't get elsewhere
  is what you learned the hard way. Keep the surprises, the mistakes,
  and the stories ("I expected stale data and got **NULL**"). Run the
  example before you write about it so the surprise is real.

- **Simplify early, correct later.** An early simplification is fine
  when it eases the reader into a hard concept. Save the sharp corners
  (the "acktually") for after they have the broad picture, and then
  say so.

## Avoid these linguistic conventions

- "It's X, not Y" and its cousins ("X, not Y")
- "X in an overcoat" / "X masquerading as Y"
- Throat-clearing openers like "The short version is"
- Evenly sized one-topic-per-paragraph structure
- doing work

These are rules of thumb. Break one on purpose when the sentence reads
best.

## Avoid these words

- genuinely
- ceremony
- quietly
- honest (and honestly)

## Avoid marketing adjectives

- Avoid marketing adjectives ('professional', 'modern') in docs/comments.
  Use specific, concrete descriptions instead.

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

- **Length follows the topic.** An article is as long as it needs to be
  for the reader to ask good questions about the topic or start using
  the idea. There is no word target. When two lengths would both do,
  take the shorter one, since long articles are tiring to read. A
  section that raises and answers its own questions is a candidate for
  an article of its own, the way the `brk` material was split out of
  the memory allocation article.

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

- **Examples model the habits you want the reader to copy.** Someone
  will type in your code and keep the habits it teaches. Check every
  allocation and every `fopen()`. Free what you allocate. Guard
  pointer arguments at the top of a function. If an example leaves
  something out on purpose, a comment says why.

- **Don't generalize an example.** When it's about four things, write
  `4`. A macro that makes it extensible only makes it harder to read.

- **C style:**
  - Asterisk binds to variable name: `int *p`, not `int* p`
  - NULL is explicitly cast: `(int *)NULL`. Pointer arrays start with
    explicit NULLs even though the compiler would zero them
  - Typedefs end with `_t`: `options_t`, `point_t`
  - Constants and macros in ALL_CAPS
  - Block comments use `/* */`, not `//`
  - EXIT_SUCCESS and EXIT_FAILURE, not 0 and -1
  - Bodies of one statement omit the braces and go on their own
    indented line. Bodies of two or more statements keep them.
  - Declare pointers as NULL and allocate in the body, inside the
    test: `if (!(p = (int *)malloc(n * sizeof(*p))))`. Don't allocate
    in the declaration
  - Cast the return value of `malloc()`, `calloc()` and `realloc()` to
    the pointer type, the same way NULL is cast. C doesn't require it.
    It tells the reader what you meant. No cast is needed when the
    destination is already a `void *`
  - Size allocations with the variable: `sizeof(*p)`, not
    `sizeof(int)`
  - Report a failure with `perror("name")`, where name is the
    variable that failed, and then bail. Use `fprintf(stderr, ...)`
    when the message needs more, such as the count that was too big
  - Guard pointer arguments at the top of a function. A function that
    returns a status also sets `errno = EINVAL`. A function that
    mirrors `free()` accepts NULL and returns
  - Write to an explicit stream: `fputc(c, stdout)` rather than
    `putchar(c)`. The output may go to a file one day

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

- **Pointer arrows use dashed lines.** The arrowhead takes up a column,
  so the other end of the arrow needs one more dash to keep both elbows
  lined up with the vertical bar. With the pointer above its target:

  ```
  │ int *p │  0x4000  │ 0x4004 │─ ─ ─┐
  ├────────┼──────────┼────────┤     │
  │ int x  │  0x4004  │     42 │◄─ ──┘
  ```

  With the target above the pointer, swap the ends: `◄─ ──┐` on top and
  `─ ─ ─┘` on the bottom. A straight arrow is `─ ─ ▸`. Check the
  columns. A corner one character off is easy to miss in an editor and
  obvious once the page is rendered.

- **Declaration order matters.** If x is declared before p, x
  appears above p in the diagram. Top-to-bottom should match the
  reader's mental model of what happened first.

## Links

- **Cross-reference other articles in the series.** Use relative
  paths: `../how-i-write-main/article.md`. This builds the web of
  knowledge and gives readers a trail to follow.

- **Link a phrase that belongs in the sentence.** Readers won't consume
  the series in the order it was written, so never write "the last
  article" or "the next article". Link the words the sentence needs
  instead: `[a map of memory][address-space] ended with a challenge`, or
  `[memory layout][address-space]`. Use lowercase, with a capital only
  at the start of a sentence, and skip the full playful title. The color
  of the link already tells the reader there is more behind the phrase.

- **Link big chunks, not every term.** Link to things a reader can chew
  on: an article, a manual page, a standard. Don't link every term. If
  they wonder what `sizeof` is, they can search for it. Raising the
  question is enough.

- **Put the link on the name of the thing.** Link `man man` or
  a map of memory, not a generic label such as "here", "web version" or
  "the article".

- **Future article links are placeholders, and every placeholder has a
  stub.** When you promise an article, create its directory with an
  `article.md` (metadata block with `Status: stub`, a title, and a
  comment recording where it was promised) and a `README.md` symlink to
  it, add a Planned row to the README, and link it by relative path:
  `../linker-aliens/article.md`. A bare slug is not a link, because
  nothing resolves it. `uv run article-tools stub c/slug` does all of
  this. These are commitments to write, not decoration.

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

- **Sizes use KB, MB and GB for the 1024-based units.** No KiB or MiB.
  Say 128 KB, not 128 KiB.

- **Region names are bold capitals in prose:** **TEXT**, **DATA**,
  **BSS**, **HEAP**, **STACK**. In diagrams they are capitals without
  bold, since a diagram can't carry it.

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
  Status: stub | draft | review | published
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

Short tips a new programmer would need are welcome even when they wander
a little off the topic: how to find a manual page, what a compiler flag
does. Keep them brief, and don't send the reader off to read a whole
other article for them.

## The Test

Before calling an article done, ask:

1. Does every code example compile and produce the shown output?
2. Would I have wanted to read this when I was learning?
3. Does the reader know what to do next?

If yes to all three, ship it.

## Pre-Push Checklist (Johnny)

Before pushing any article changes to GitHub:

1. Run a style guide pass on touched articles (`uv run article-tools audit`
   in `tools/` counts what a script can check)
2. Check heading levels (H1 for title, H2 for sections, H3 for subsections)
3. Verify code examples are complete and correct
4. Confirm link references at bottom are present and accounted for, and
   that every one resolves: a relative path to a file that exists, or an
   external URL. A promised article gets a stub. `uv run article-tools
   check` tests links, diagrams and layout and exits 1 on a problem. The
   pre-push hook runs it for you once you have run `pre-commit install`
5. Spell-check (typos happen to the best of us)
