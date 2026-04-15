import os
import time
from pathlib import Path

from adapters.cavia.cavia_scenario_loader import CaviaScenarioLoader
from adapters.cavia.find_valid_scenarios import find_or_load_scenarios, get_scenario_paths
from adapters.cavia.utils.distributions import STRATEGY_REGISTRY
from adapters.cavia.utils.path import PKL_PATH
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.simulator import Simulator

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)


def main():
    global_start = time.perf_counter()

    valid_scenarios = find_or_load_scenarios(PKL_PATH, force_rescan=True)

    distributions = ["exponential", "normal", "uniform"]
    for d in distributions:
        if d not in STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{d}' non trovata nel registry. Strategie disponibili: {list(STRATEGY_REGISTRY.keys())}")

    BASE_SEED = 42
    NUM_RUNS = 10

    for dist_type in distributions:
        print(f"\nDISTRIBUTION: {dist_type}")
        total = 0
        done = 0
        for scenario_rel_path, apps in valid_scenarios.items():

            scenario_name = os.path.basename(scenario_rel_path)

            success_apps = []
            invalid_apps = []

            for app_name in apps:
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

                        def my_algorithm(parameters):
                            return

                        def static_dummy_mobility(user):
                            user.coordinates_trace.append(user.coordinates)

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

                    success_apps.append(app_name)

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
