import os
import json
import pickle

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_SCENARIOS = os.path.join(CURRENT_DIR, "valid_scenarios_cache.json")


def find_or_load_scenarios(base_path, force_rescan=False):

    if os.path.exists(VALID_SCENARIOS) and not force_rescan:
        print(f"Found valid_scenarios_cache.json in: {VALID_SCENARIOS}")
        with open(VALID_SCENARIOS, "r") as f:
            return json.load(f)

    valid_folders = []

    subfolders = [f.path for f in os.scandir(base_path) if f.is_dir()]

    for folder in subfolders:
        is_valid = False
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".pkl"):
                    with open(os.path.join(root, file), "rb") as f:
                        data = pickle.load(f)
                        if data.get("status") == 2:
                            parts = folder.split(os.sep)
                            if "CAVIA" in parts:
                                rel_path = os.path.join(*parts[parts.index("CAVIA") :])
                                valid_folders.append(rel_path)
                            else:
                                valid_folders.append(os.path.basename(folder))

                            is_valid = True
                            break
            if is_valid:
                break

    valid_folders = sorted(list(set(valid_folders)))
    with open(VALID_SCENARIOS, "w") as f:
        json.dump(valid_folders, f, indent=4)

    print(f"Found {len(valid_folders)} valid scenarios in '{VALID_SCENARIOS}'")
    return valid_folders


# PKL_BASE_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "CAVIA", "src", "LR")
# scenarios = find_or_load_scenarios(PKL_BASE_PATH)

# CAVIA/src/LR/1_26_solution_v1
# print(f"Trovati {len(scenarios)} scenari validi: ")
# for s in scenarios:
#     print(s)
