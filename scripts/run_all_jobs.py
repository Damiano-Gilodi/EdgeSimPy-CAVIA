import os
import subprocess
import sys
from pathlib import Path
import time

from adapters.cavia.find_valid_scenarios import find_or_load_scenarios
from adapters.cavia.utils.distributions import STRATEGY_REGISTRY
from adapters.cavia.utils.path import PKL_PATH


BASE_DIR = Path(__file__).resolve().parent.parent


def run_script(script_path, distribution, scenario, app, num_runs=100):
    cmd = [
        sys.executable,
        str(script_path),
        "--distribution",
        distribution,
        "--scenario",
        scenario,
        "--app",
        app,
        "--num-runs",
        str(num_runs),
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"Error during execution of job: {distribution} | {scenario} | {app}")


def main():

    start = time.perf_counter()

    valid_scenarios = find_or_load_scenarios(PKL_PATH, force_rescan=True)
    distributions = ["exponential", "uniform", "gamma_k2", "normal", "normal_wide", "normal_wide_trunc"]

    for d in distributions:
        if d not in STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{d}' not found in registry. " f"Strategy available: {list(STRATEGY_REGISTRY.keys())}")

    sim_script = BASE_DIR / "simulation" / "cavia_simulation" / "cavia_simulation.py"

    for dist_type in distributions:
        for scenario_rel_path, apps in valid_scenarios.items():
            scenario_name = os.path.basename(scenario_rel_path)

            print(f"START: {dist_type} | {scenario_name}")

            for app_name in apps:
                run_script(sim_script, dist_type, scenario_name, app_name, num_runs=10)

    end = time.perf_counter()
    print(f"\nALL JOBS COMPLETED : {end - start:.2f} s ({(end - start)/60:.2f} min)")


if __name__ == "__main__":
    main()
