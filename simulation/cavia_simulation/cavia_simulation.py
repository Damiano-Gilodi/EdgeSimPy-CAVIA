import gc
import json
import os
import shutil
import time
from pathlib import Path

from adapters.cavia.cavia_scenario_loader import CaviaScenarioLoader
from adapters.cavia.find_valid_scenarios import find_or_load_scenarios, get_scenario_paths
from adapters.cavia.utils.distributions import STRATEGY_REGISTRY
from adapters.cavia.utils.path import PKL_PATH
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.simulator import Simulator
from edge_sim_py.utils.edge_sim_py_resetter import EdgeSimPyResetter

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

RESET_OUTPUTS = True
PROGRESS_FILE = BASE_DIR / "simulation_progress.json"


def make_progress_key(distribution, scenario, app):
    return f"{distribution}|{scenario}|{app}"


def load_completed_apps(progress_file):
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_completed_apps(progress_file, completed_apps):
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(sorted(completed_apps), f, indent=4)


def is_app_marked_completed(completed_apps, distribution, scenario, app):
    return make_progress_key(distribution, scenario, app) in completed_apps


def mark_app_completed(completed_apps, distribution, scenario, app):
    completed_apps.add(make_progress_key(distribution, scenario, app))


def my_algorithm(parameters):
    return


def static_dummy_mobility(user):
    user.coordinates_trace.append(user.coordinates)


def main():
    global_start = time.perf_counter()

    logs_dir = BASE_DIR / "logs"
    datasets_dir = BASE_DIR / "datasets"

    if RESET_OUTPUTS:
        if logs_dir.exists():
            shutil.rmtree(logs_dir)
        if datasets_dir.exists():
            shutil.rmtree(datasets_dir)
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()

    completed_apps = load_completed_apps(PROGRESS_FILE)

    valid_scenarios = find_or_load_scenarios(PKL_PATH, force_rescan=True)

    distributions = ["exponential", "uniform", "gamma_k2", "normal", "normal_wide", "normal_wide_trunc"]
    for d in distributions:
        if d not in STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{d}' non trovata nel registry. Strategie disponibili: {list(STRATEGY_REGISTRY.keys())}")

    BASE_SEED = 42
    NUM_RUNS = 100

    for dist_type in distributions:
        print(f"\nDISTRIBUTION: {dist_type}")
        total = 0
        done = 0
        for scenario_rel_path, apps in valid_scenarios.items():

            scenario_name = os.path.basename(scenario_rel_path)

            success_apps = []
            invalid_apps = []

            for app_name in apps:

                if is_app_marked_completed(completed_apps, dist_type, scenario_name, app_name):
                    success_apps.append(app_name)
                    continue

                try:
                    for run_index in range(NUM_RUNS):

                        phys_path, app_path, pkl_path = get_scenario_paths(scenario_name, app_name)

                        current_seed = BASE_SEED + run_index

                        CaviaScenarioLoader(
                            physical_graph_path=phys_path,
                            app_graph_path=app_path,
                            pkl_path=pkl_path,
                            seed=current_seed,
                            dist=dist_type,
                        ).build_scenario()

                        ComponentManager.export_scenario(save_to_file=True, file_name=scenario_name)

                        # Directory log: logs/1_26_solution_v0/1SSS/
                        current_logs_dir = BASE_DIR / "logs" / dist_type / scenario_name / app_name / f"run_{run_index}"
                        current_logs_dir.mkdir(parents=True, exist_ok=True)

                        simulator = Simulator(
                            dump_interval=1,
                            tick_unit="milliseconds",
                            tick_duration=1,
                            stopping_criterion=lambda model: all(d._status == "finished" for d in DataPacket.all()) or model.schedule.steps >= 500,
                            resource_management_algorithm=my_algorithm,
                            user_defined_functions=[static_dummy_mobility],
                            logs_directory=str(current_logs_dir),
                        )

                        simulator.initialize(input_file=f"datasets/{scenario_name}.json")
                        simulator.run_model()

                        del simulator
                        EdgeSimPyResetter.clear_all()
                        ComponentManager._ComponentManager__model = None
                        gc.collect()

                    success_apps.append(app_name)

                    mark_app_completed(completed_apps, dist_type, scenario_name, app_name)
                    save_completed_apps(PROGRESS_FILE, completed_apps)

                except ValueError as e:
                    print(f"Skipping {app_name}: {e}")
                    invalid_apps.append(app_name)
                    continue

                except Exception as e:
                    print(f"Error during the simulation of {app_name}: {e}")

            total = total + len(apps)
            done = done + len(success_apps)

        print(f"Success: {done}/{total} Apps completate")

    global_end = time.perf_counter()
    total_seconds = global_end - global_start
    print("\n\n ALL SIMULATIONS COMPLETED.")
    print(f"Total time: {total_seconds:.2f} s ({total_seconds/60:.2f} min)")


if __name__ == "__main__":
    main()
