import timeit
import gc
import platform
import sys
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os
from functools import cached_property

# --------- Lazy Property Implementations ---------

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
    return (total_time / iterations) * 1e9  # ns

def benchmark_warm_access(cls, iterations=10_000, inner_loops=100):
    gc.disable()
    def run():
        obj = cls()
        obj.foo
        for _ in range(inner_loops):
            obj.foo
    timer = timeit.Timer(run)
    total_time = timer.timeit(number=iterations)
    gc.enable()
    return (total_time / (iterations * inner_loops)) * 1e9  # ns

def compute_total_time(cold_ns, warm_ns, access_counts):
    return [cold_ns + warm_ns * (n - 1) for n in access_counts]

def format_ns(ns):
    return f"{ns:,.1f} ns"

# --------- Environment Info ---------

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

access_counts = [1, 2, 5, 10, 100, 1_000, 10_000, 100_000]
total_times = {
    name: compute_total_time(cold_results[name], warm_results[name], access_counts)
    for name in classes
}

# --------- Output Table to Console ---------

print("\nCold Access (ns):")
for name, ns in cold_results.items():
    print(f"{name:<8}: {format_ns(ns)}")

print("\nWarm Access (ns):")
for name, ns in warm_results.items():
    print(f"{name:<8}: {format_ns(ns)}")

print("\nTotal Time vs Access Count:")
print(f"{'Accesses':<10} {'EAFP':>12} {'LBYL':>12} {'Cached':>12}")
for i, count in enumerate(access_counts):
    row = [total_times[name][i] for name in classes]
    print(f"{count:<10} {format_ns(row[0]):>12} {format_ns(row[1]):>12} {format_ns(row[2]):>12}")

# --------- Plotting Utilities ---------

def plot_bar_with_table_clean(title, ylabel, data_dict, filename):
    names = list(data_dict.keys())
    values = [data_dict[name] for name in names]
    formatted_values = [format_ns(v) for v in values]

    fig = plt.figure(figsize=(6, 5))
    gs = GridSpec(3, 1, height_ratios=[3, 1, 0.2])
    ax_bar = fig.add_subplot(gs[0])
    ax_table = fig.add_subplot(gs[1])

    bars = ax_bar.bar(names, values, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    ax_bar.set_ylabel(ylabel)
    ax_bar.set_title(title)
    ax_bar.set_ylim(0, max(values) * 1.3)

    for bar, val in zip(bars, values):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, val + max(values) * 0.02, f"{val:.1f}", ha='center', va='bottom')

    ax_table.axis("off")

    table_data = [["Method", "Time (ns)"]]
    for name, val in zip(names, formatted_values):
        table_data.append([name, val])

    table = ax_table.table(cellText=table_data,
                           colWidths=[0.4, 0.4],
                           cellLoc='center',
                           loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)

    fig.text(0.5, 0.02, env_str, ha='center', fontsize=8, color='gray')
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(f"graphs/{filename}", dpi=150)
    plt.close()
    print(f"Saved graphs/{filename}")

def plot_line_with_table_clean(title, ylabel, xvals, data_dict, filename):
    fig = plt.figure(figsize=(8, 6))
    gs = GridSpec(3, 1, height_ratios=[3, 1.5, 0.2])
    ax_line = fig.add_subplot(gs[0])
    ax_table = fig.add_subplot(gs[1])

    for name, series in data_dict.items():
        ax_line.plot(xvals, series, marker='o', label=name)

    ax_line.set_xlabel("Number of Accesses")
    ax_line.set_ylabel(ylabel)
    ax_line.set_title(title)
    ax_line.set_xscale("log")
    ax_line.set_yscale("log")
    ax_line.grid(True, which="both", linestyle="--", alpha=0.5)
    ax_line.legend()

    ax_table.axis("off")

    headers = ["Accesses"] + list(data_dict.keys())
    table_data = [headers]
    for i, x in enumerate(xvals):
        row = [f"{x:,}"] + [format_ns(data_dict[name][i]) for name in data_dict]
        table_data.append(row)

    table = ax_table.table(cellText=table_data,
                           colWidths=[0.2] + [0.2] * len(data_dict),
                           cellLoc='center',
                           loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.2, 1.4)

    fig.text(0.5, 0.02, env_str, ha='center', fontsize=8, color='gray')
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(f"graphs/{filename}", dpi=150)
    plt.close()
    print(f"Saved graphs/{filename}")

# --------- Generate Graphs ---------

os.makedirs("graphs", exist_ok=True)

plot_bar_with_table_clean(
    "Cold Access Time (ns)",
    "Nanoseconds per call",
    cold_results,
    "cold_access.png"
)

plot_bar_with_table_clean(
    "Warm Access Time (ns)",
    "Nanoseconds per call",
    warm_results,
    "warm_access.png"
)

plot_line_with_table_clean(
    "Total Time vs Access Count",
    "Total Time (ns)",
    access_counts,
    total_times,
    "total_time_vs_accesses.png"
)