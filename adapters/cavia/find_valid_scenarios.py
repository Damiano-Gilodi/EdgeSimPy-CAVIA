import os
import json
import pickle

from adapters.cavia.utils.path import BASE_PATH, PKL_PATH

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_SCENARIOS = os.path.join(CURRENT_DIR, "dump_scenarios", "valid_scenarios_cache.json")


def find_or_load_scenarios(pkl_path=PKL_PATH, force_rescan=False):

    if os.path.exists(VALID_SCENARIOS) and not force_rescan:
        with open(VALID_SCENARIOS, "r") as f:
            return json.load(f)

    valid_data = {}

    subfolders = [f.path for f in os.scandir(pkl_path) if f.is_dir()]

    for folder in subfolders:
        valid_apps_in_folder = []

        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith("_slss.pkl") and file.startswith("var_coeff_values_"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "rb") as f:
                        data = pickle.load(f)
                        if data.get("status") == 2:
                            app_name = file.replace("var_coeff_values_", "").replace("_slss.pkl", "")
                            valid_apps_in_folder.append(app_name)

        if valid_apps_in_folder:
            parts = folder.split(os.sep)
            rel_path = os.path.join(*parts[parts.index("CAVIA") :]) if "CAVIA" in parts else os.path.basename(folder)
            valid_data[rel_path] = sorted(valid_apps_in_folder)

    valid_data = dict(sorted(valid_data.items()))
    output_dir = os.path.dirname(VALID_SCENARIOS)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(VALID_SCENARIOS, "w") as f:
        json.dump(valid_data, f, indent=4)

    return valid_data


def get_scenario_paths(scenario_name, app_type, pkl_path=PKL_PATH, force_rescan=False):

    scenarios = find_or_load_scenarios(pkl_path, force_rescan=force_rescan)
    matched_keys = [k for k in scenarios.keys() if scenario_name in k]
    if not matched_keys:
        raise ValueError(f"Scenario '{scenario_name}' not found.")

    scenario_rel_path = matched_keys[0]
    valid_apps = scenarios[scenario_rel_path]

    if app_type not in valid_apps:
        raise ValueError(f"App '{app_type}' in scenario '{scenario_name}' not valid.")

    scenario_dir = os.path.join(BASE_PATH.parent, scenario_rel_path)
    phys_path = os.path.join(scenario_dir, "physical_graph.graphml")
    app_path = os.path.join(scenario_dir, "ms", f"{app_type}.graphml")
    pkl_path = os.path.join(scenario_dir, f"var_coeff_values_{app_type}_slss.pkl")

    for p in [phys_path, app_path, pkl_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")

    return phys_path, app_path, pkl_path
