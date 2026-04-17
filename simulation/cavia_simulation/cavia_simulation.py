import argparse
import gc
import json
import os
import shutil
from pathlib import Path

from adapters.cavia.cavia_scenario_loader import CaviaScenarioLoader
from adapters.cavia.find_valid_scenarios import get_scenario_paths
from adapters.cavia.utils.distributions import STRATEGY_REGISTRY
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.simulator import Simulator
from edge_sim_py.utils.edge_sim_py_resetter import EdgeSimPyResetter

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--distribution", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--app", required=True)
    parser.add_argument("--num-runs", type=int, default=100)
    parser.add_argument("--base-seed", type=int, default=42)
    parser.add_argument("--reset-app-logs", action="store_true")  # reset app logs
    parser.add_argument("--force", action="store_true")  # force running even if the app is already completed
    return parser.parse_args()


def main():

    args = parse_args()

    dist_type = args.distribution
    scenario_name = args.scenario
    app_name = args.app
    num_runs = args.num_runs
    base_seed = args.base_seed

    if dist_type not in STRATEGY_REGISTRY:
        raise ValueError(f"Strategy '{dist_type}' not found in registry. " f"Strategy available: {list(STRATEGY_REGISTRY.keys())}")

    completed_apps = load_completed_apps(PROGRESS_FILE)

    if not args.force and is_app_marked_completed(completed_apps, dist_type, scenario_name, app_name):
        print(f"Already completed: {dist_type} | {scenario_name} | {app_name}")
        return

    app_logs_dir = BASE_DIR / "logs" / dist_type / scenario_name / app_name
    if args.reset_app_logs and app_logs_dir.exists():
        shutil.rmtree(app_logs_dir)

    phys_path, app_path, pkl_path = get_scenario_paths(scenario_name, app_name)

    for run_index in range(num_runs):
        current_seed = base_seed + run_index

        CaviaScenarioLoader(
            physical_graph_path=phys_path,
            app_graph_path=app_path,
            pkl_path=pkl_path,
            seed=current_seed,
            dist=dist_type,
        ).build_scenario()

        ComponentManager.export_scenario(save_to_file=True, file_name=scenario_name)

        current_logs_dir = app_logs_dir / f"run_{run_index}"
        current_logs_dir.mkdir(parents=True, exist_ok=True)

        simulator = Simulator(
            dump_interval=100,
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

    mark_app_completed(completed_apps, dist_type, scenario_name, app_name)
    save_completed_apps(PROGRESS_FILE, completed_apps)


if __name__ == "__main__":
    main()
