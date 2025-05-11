# Benchmarking Lazy Property Patterns in Python: EAFP vs LBYL vs `@cached_property`

In performance-sensitive Python applications, it is often beneficial to defer the computation of an attribute until it is first accessed. This technique, known as lazy evaluation, is useful when a value is expensive to compute and may not always be needed.

Python developers have several patterns at their disposal to implement lazily computed properties. This article benchmarks and compares three common approaches:

- EAFP ("Easier to Ask Forgiveness than Permission") using `try/except`
- LBYL ("Look Before You Leap") using `hasattr()`
- `functools.cached_property` introduced in Python 3.8

This analysis includes microbenchmark timing data for cold and warm access scenarios, as well as total access time across different usage profiles. The goal is to provide actionable insights into which pattern is most appropriate under different conditions.

> 📂 All benchmark code and graphs are available in this GitHub repository: [Lazy Properties][repo]

---

## Problem Statement

Suppose a class contains an attribute that is expensive to compute. It should be computed only when accessed for the first time, and its value should be cached thereafter. This is a common requirement in applications such as data models, caching layers, or property-based computations in scientific computing.

The following function simulates an expensive computation:

```python
def compute():
    return 42
```

---

## Lazy Evaluation Techniques

### 1. EAFP: Using `try/except`

This approach follows the Pythonic principle of “Easier to Ask Forgiveness than Permission.” It attempts to return a cached value directly and catches an `AttributeError` if the value hasn’t been set yet. If the error is raised, it computes and stores the value before returning it.

```python
class EAFP:
    @property
    def foo(self):
        try:
            return self._foo
        except AttributeError:
            self._foo = compute()
            return self._foo
```

**How it works**:

- On first access, `_foo` does not exist, so an `AttributeError` is raised and caught.
- The value is computed and stored.
- On subsequent accesses, `_foo` is returned without error.

| ✅ **Pros**                             | ❌ **Cons**                                   |
|----------------------------------------|-----------------------------------------------|
| Concise implementation                 | Exception handling is expensive               |
| Familiar idiom in many Python codebases| Can mask real `AttributeError`s              |
| Compatible with all Python versions    | Harder to debug in complex object hierarchies |

---

### 2. LBYL: Using `hasattr()`

This method explicitly checks whether the backing attribute exists before accessing it. If not, it computes and stores the value.

```python
class LBYL:
    @property
    def foo(self):
        if not hasattr(self, '_foo'):
            self._foo = compute()
        return self._foo
```

**How it works**:

- `hasattr()` checks whether `_foo` exists.
- If it doesn't exist, the value is computed and assigned.
- The value is then returned, whether from cache or freshly computed.

| ✅ **Pros**                          | ❌ **Cons**                                   |
|--------------------------------------|-----------------------------------------------|
| Fastest cold access on M3 hardware   | Slightly more verbose                         |
| Avoids exception overhead            | Can fail if `_foo` exists but is invalid      |
| Compatible with older Python versions| Requires custom logic for invalidation        |
| Allows manual cache control          | Less elegant than `@cached_property`          |

---

### 3. `@cached_property` from `functools` (Python 3.8+)

This is the most modern approach. Python’s `functools.cached_property` decorator automatically handles the caching of a property’s return value after its first call.

```python
from functools import cached_property

class Cached:
    @cached_property
    def foo(self):
        return compute()
```

**How it works**:

- On first access, the method is executed and the result is cached.
- The cached value replaces the property method on the instance.
- Future accesses return the cached value without re-running the method.

| ✅ **Pros**                      | ❌ **Cons**                                   |
|----------------------------------|-----------------------------------------------|
| Fast warm access performance     | Requires Python 3.8 or newer                  |
| Clean, declarative syntax        | Manual invalidation required (`del`)          |
| Built-in and battle-tested       | Not suitable for custom caching logic         |
| Thread-safe in CPython           |                                               |

---

## 🧪 Benchmark Setup

All benchmarks were collected using **Python 3.13.3** on a **2024 MacBook Air M3 (Apple Silicon)** running **macOS 14.4.1 (Sequoia)**. The tests were executed using the standard library’s `timeit` module with garbage collection disabled to reduce noise.

> ⚠️ Results may vary depending on Python version, CPU architecture, operating system, and runtime optimizations. For accurate comparisons, you should run the provided benchmark code on your own system.

### Environment

- **System**: MacBook Air M3 (2024), macOS 14.x
- **Python**: 3.13.3 (arm64)
- **Timing tool**: `timeit`
- **Iterations**: 1,000,000 (cold), 10,000 loops × 100 accesses (warm)
- **GC**: Disabled during timing

You can run the full benchmark and generate the graphs using this script:  
📄 [`lazy_property_benchmark.py`][script]

---

## Cold Access Performance (First Access)

![Cold Access Graph][cold]

---

## Warm Access Performance (Cached Property Read)

![Warm Access Graph][warm]

---

## Total Time vs Number of Accesses (Derived)

![Total Time Graph][total]

---

## Practical Guidance

Choosing the right lazy evaluation pattern depends on your Python version, performance needs, and code clarity:

- ✅ **Use `@cached_property`** by default if you're on Python 3.8+. It offers excellent warm access speed and clean syntax.
- ✅ **Use LBYL** for the fastest cold access and compatibility with older Python versions.
- ⚠️ **Avoid EAFP** in performance-critical code. While idiomatic, it incurs the highest cold access cost due to exception overhead.

---

## Additional Resources

- [functools.cached_property Documentation](https://docs.python.org/3/library/functools.html#functools.cached_property)
- [Memoization – Wikipedia](https://en.wikipedia.org/wiki/Memoization)
- [Lazy Evaluation – Wikipedia](https://en.wikipedia.org/wiki/Lazy_evaluation)
- [Python Descriptor HowTo Guide](https://docs.python.org/3/howto/descriptor.html)

[repo]: https://github.com/JnyJny/articles/tree/master/python/lazy_properties
[script]: https://github.com/JnyJny/articles/python/lazy_properties/blob/main/benchmark.py  
[cold]: https://github.com/JnyJny/articles/blob/74e1349325fcde63818da0f37f1a8a783710b5ba/python/lazy_properties/graphs/cold_access.png
[warm]: https://github.com/JnyJny/articles/blob/74e1349325fcde63818da0f37f1a8a783710b5ba/python/lazy_properties/graphs/warm_access.png
[total]: https://github.com/JnyJny/articles/blob/74e1349325fcde63818da0f37f1a8a783710b5ba/python/lazy_properties/graphs/total_time_vs_accesses.png
