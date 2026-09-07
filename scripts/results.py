"""Show the paper plots and print tracking/timing metrics.

Place the three Webots run files and three server timing files in the
repository root before running this script.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODES = ("kanayama", "plaintext", "ckks")
LABELS = {
    "kanayama": "Kanayama",
    "plaintext": "Plaintext NN",
    "ckks": "CKKS NN",
}
SERVER_WARMUP_REQUESTS = 2
WHEEL_LIMIT = 10.0

DASH_KAN = (0, (6, 3))
DASH_PLAIN = (3, (6, 3))
DASH_CKKS = (6, (6, 3))
DASH_LIMIT = (0, (3, 3))


def require_file(path):
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return path


def load_run(mode):
    return np.load(require_file(ROOT / f"run_data_webots_{mode}.npz"))


def load_server_times(mode):
    data = np.load(require_file(ROOT / f"server_processing_times_{mode}.npz"))
    values = np.asarray(data["processing_time_ms"], dtype=float)
    if len(values) <= SERVER_WARMUP_REQUESTS:
        raise SystemExit(f"Not enough server timing samples for {mode}")
    return values[SERVER_WARMUP_REQUESTS:]


def tracking_error_m(run):
    actual = np.asarray(run["actual_positions"], dtype=float)
    reference = np.asarray(run["reference_positions"], dtype=float)
    n = min(len(actual), len(reference))
    return np.linalg.norm(actual[:n] - reference[:n], axis=1)


def tracking_metrics_cm(error_m):
    error_cm = 100.0 * np.asarray(error_m, dtype=float)
    return (
        float(np.sqrt(np.mean(error_cm**2))),
        float(np.mean(error_cm)),
        float(np.max(error_cm)),
    )


def time_axis(run, length):
    dt = float(run["sim_timestep_ms"]) / 1000.0
    return np.arange(length) * dt


def print_results(runs, errors):
    print("Tracking error (cm)")
    print(f"{'Mode':14s} {'RMSE':>9s} {'Mean':>9s} {'Max':>9s}")
    for mode in MODES:
        rmse, mean, maximum = tracking_metrics_cm(errors[mode])
        print(f"{LABELS[mode]:14s} {rmse:9.4f} {mean:9.4f} {maximum:9.4f}")

    print("\nProcessing time (ms)")
    print(
        f"{'Mode':14s} {'Server mean':>12s} {'RTT mean':>10s} "
        f"{'RTT min':>10s} {'RTT max':>10s}"
    )
    server_times = {}
    for mode in MODES:
        server = load_server_times(mode)
        server_times[mode] = server
        rtt = np.asarray(runs[mode]["round_trip_times_ms"], dtype=float)
        print(
            f"{LABELS[mode]:14s} {np.mean(server):12.2f} {np.mean(rtt):10.2f} "
            f"{np.min(rtt):10.2f} {np.max(rtt):10.2f}"
        )

    ckks = runs["ckks"]
    prep = np.asarray(ckks["request_preparation_times_ms"], dtype=float)
    network_server = np.asarray(ckks["network_server_times_ms"], dtype=float)
    response = np.asarray(ckks["response_processing_times_ms"], dtype=float)
    rtt = np.asarray(ckks["round_trip_times_ms"], dtype=float)
    server = server_times["ckks"]

    n = min(len(network_server), len(server))
    socket_overhead = network_server[:n] - server[:n]

    print("\nCKKS timing breakdown (mean, ms)")
    print(f"  Request preparation : {np.mean(prep):.2f}")
    print(f"  Server processing   : {np.mean(server):.2f}")
    print(f"  Socket/wait overhead: {np.mean(socket_overhead):.2f}")
    print(f"  Response processing : {np.mean(response):.2f}")
    print(f"  Total RTT           : {np.mean(rtt):.2f}")


def show_trajectory(runs):
    plt.figure(figsize=(6.5, 6.0))
    reference = runs["kanayama"]["reference_positions"]
    plt.plot(reference[:, 0], reference[:, 1], "k--", linewidth=2.2, label="Reference")
    for mode in MODES:
        actual = runs[mode]["actual_positions"]
        plt.plot(actual[:, 0], actual[:, 1], linewidth=1.8, label=LABELS[mode])
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.title("Trajectory Tracking Performance on the Lissajous Path")
    plt.axis("equal")
    plt.grid(True)
    plt.legend(fontsize=9)
    plt.tight_layout()


def show_tracking_error(runs, errors):
    plt.figure(figsize=(7.0, 4.5))
    for mode in MODES:
        err = errors[mode]
        plt.plot(time_axis(runs[mode], len(err)), err, linewidth=1.8, label=LABELS[mode])
    plt.xlabel("Time (s)")
    plt.ylabel("Position tracking error (m)")
    plt.title("Tracking Error on the Lissajous Path")
    plt.grid(True)
    plt.legend(fontsize=9)
    plt.tight_layout()


def show_wheel_speeds(runs):
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.0), sharex=True)
    line_styles = {
        "kanayama": DASH_KAN,
        "plaintext": DASH_PLAIN,
        "ckks": DASH_CKKS,
    }

    for axis, wheel_index, ylabel in (
        (axes[0], 0, r"Right wheel speed $\omega_r$ (rad/s)"),
        (axes[1], 1, r"Left wheel speed $\omega_l$ (rad/s)"),
    ):
        for mode in MODES:
            t = np.asarray(runs[mode]["control_update_t"], dtype=float)
            wheel = np.asarray(runs[mode]["wheel_speeds"][:, wheel_index], dtype=float)
            n = min(len(t), len(wheel))
            axis.plot(
                t[:n],
                wheel[:n],
                linewidth=1.6,
                linestyle=line_styles[mode],
                label=LABELS[mode],
            )
        axis.axhline(
            WHEEL_LIMIT,
            linewidth=1.0,
            linestyle=DASH_LIMIT,
            label="Wheel-speed limits" if wheel_index == 0 else None,
        )
        axis.axhline(-WHEEL_LIMIT, linewidth=1.0, linestyle=DASH_LIMIT)
        axis.set_ylabel(ylabel)
        axis.set_ylim(-10.8, 10.8)
        axis.grid(True)
        axis.legend(fontsize=9)

    axes[1].set_xlabel("Time (s)")
    fig.tight_layout()


def main():
    print("[Results] Loading experiment files...")
    runs = {mode: load_run(mode) for mode in MODES}
    errors = {mode: tracking_error_m(runs[mode]) for mode in MODES}
    print("[Results] Files loaded. Computing metrics...")

    print_results(runs, errors)
    show_trajectory(runs)
    show_tracking_error(runs, errors)
    show_wheel_speeds(runs)
    print("\n[Results] Plots are ready. Close the plot windows to finish.")
    plt.show()


if __name__ == "__main__":
    main()
