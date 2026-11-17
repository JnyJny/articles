<!--
Author: Erik O'Shaughnessy
Date: November 2026
Status: stub
Series: C Programming
Prerequisites: pointers
Next: none
-->

# Many Ways to Say Array

<!--
Promised in:
- Erik (2026-11-17): a short article establishing the pointer/array relationship and the various ways C expresses arrays of things. In his words: "it's a good C skill to recognize the various ways of expressing arrays of things". Other articles can point here. The sizeof of an array versus a pointer is in c/sizeof, which should link here.
- Ways to recognize: an array object (int values[10]); a pointer plus a count (int *values, size_t count); a malloc() block indexed like an array; a sentinel-terminated array (strings end in '\0', argv ends in NULL, POINT_SENTINEL in the pointers article); the parameter spellings int values[], int values[10] and int *values, which all mean the same thing, and char *argv[] versus char **argv.
- Gaps in the pointers article this should fill: it shows that an array name decays and that p[n] is *(p + n), but never the difference. See TODO.md, Arrays.
-->
