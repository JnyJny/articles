import timeit
import gc
import platform
import sys
from datetime import datetime
import matplotlib.pyplot as plt

# --------- Benchmark Setup ---------
from functools import cached_property

def compute():
    return 42

class EAFP:
    @property
    def foo(self):
        try:
            return self._foo
        except AttributeError:
            self._foo = compute()
            return self._foo

class LBYL:
    @property
    def foo(self):
        if not hasattr(self, '_foo'):
            self._foo = compute()
        return self._foo

class Cached:
    @cached_property
    def foo(self):
        return compute()

# --------- Benchmark Functions ---------

def benchmark_cold_access(cls, iterations=1_000_000):
    gc.disable()
    def run():
        obj = cls()
        return obj.foo
    timer = timeit.Timer(run)
    total_time = timer.timeit(number=iterations)
    gc.enable()
    return (total_time / iterations) * 1e9  # nanoseconds

def benchmark_warm_access(cls, iterations=10_000, inner_loops=100):
    gc.disable()
    def run():
        obj = cls()
        obj.foo  # prime cache
        for _ in range(inner_loops):
            obj.foo
    timer = timeit.Timer(run)
    total_time = timer.timeit(number=iterations)
    gc.enable()
    return (total_time / (iterations * inner_loops)) * 1e9  # nanoseconds

def compute_total_time(cold_ns, warm_ns, access_counts):
    return [cold_ns + warm_ns * (n - 1) for n in access_counts]

# --------- System Metadata ---------

def get_environment_info():
    return {
        "Python": sys.version.split()[0],
        "OS": platform.system() + " " + platform.release(),
        "Machine": platform.machine(),
        "Processor": platform.processor() or platform.machine(),
        "Date": datetime.now().strftime('%Y-%m-%d'),
    }

env = get_environment_info()
env_str = f"{env['OS']}, Python {env['Python']}, {env['Processor']} ({env['Machine']}) — Collected: {env['Date']}"

# --------- Run Benchmarks ---------

classes = {
    "EAFP": EAFP,
    "LBYL": LBYL,
    "Cached": Cached
}

print("Running cold access benchmarks...")
cold_results = {name: benchmark_cold_access(cls) for name, cls in classes.items()}
print("Running warm access benchmarks...")
warm_results = {name: benchmark_warm_access(cls) for name, cls in classes.items()}

# Access counts for total time simulation
access_counts = [1, 2, 5, 10, 100, 1_000, 10_000, 100_000]
total_times = {
    name: compute_total_time(cold_results[name], warm_results[name], access_counts)
    for name in classes
}

# --------- Print Tables ---------

print("\nCold Access (ns per call):")
for name, ns in cold_results.items():
    print(f"{name:<8}: {ns:.1f} ns")

print("\nWarm Access (ns per call):")
for name, ns in warm_results.items():
    print(f"{name:<8}: {ns:.1f} ns")

print("\nTotal Time vs Access Count (ns):")
print(f"{'Accesses':<10} {'EAFP':>12} {'LBYL':>12} {'Cached':>12}")
for i, count in enumerate(access_counts):
    e = total_times["EAFP"][i]
    l = total_times["LBYL"][i]
    c = total_times["Cached"][i]
    print(f"{count:<10} {e:>12.1f} {l:>12.1f} {c:>12.1f}")

# --------- Plotting ---------

def plot_bar(title, ylabel, data_dict, filename):
    names = list(data_dict.keys())
    values = [data_dict[name] for name in names]
    plt.figure(figsize=(6, 4))
    bars = plt.bar(names, values, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    plt.ylabel(ylabel)
    plt.title(title)
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.1f}", ha='center', va='bottom')

    # Add environment info footer
    plt.figtext(0.5, 0.01, env_str, ha='center', fontsize=8, color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(f"graphs/{filename}")
    print(f"Saved graphs/{filename}")
    plt.close()

# Ensure output directory exists
import os
os.makedirs("graphs", exist_ok=True)

plot_bar(
    "Cold Access Time (ns)", 
    "Nanoseconds per call", 
    cold_results, 
    "cold_access.png"
)

plot_bar(
    "Warm Access Time (ns)", 
    "Nanoseconds per call", 
    warm_results, 
    "warm_access.png"
)

# Total access time plot
plt.figure(figsize=(7, 5))
for name in classes:
    plt.plot(access_counts, total_times[name], label=name)
plt.xlabel("Number of Accesses")
plt.ylabel("Total Time (ns)")
plt.title("Total Time vs Access Count")
plt.xscale("log")
plt.yscale("log")
plt.grid(True, which="both", linestyle="--", alpha=0.5)
plt.legend()
plt.figtext(0.5, 0.01, env_str, ha='center', fontsize=8, color='gray')
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig("graphs/total_time_vs_accesses.png")
print("Saved graphs/total_time_vs_accesses.png")
plt.close()