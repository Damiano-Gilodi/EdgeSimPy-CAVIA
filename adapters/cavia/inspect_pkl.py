import pickle
from pathlib import Path

SCENARIO_PATH = Path("scenarios/cavia/1_26_solution_v0")

pkl_file = SCENARIO_PATH / "var_coeff_values_1MMM_slss.pkl"

with open(pkl_file, "rb") as f:
    data = pickle.load(f)

print("TYPE:", type(data))

if isinstance(data, dict):
    print("\nKeys:")
    for k in data.keys():
        print(" -", k)

print("\nFull object preview:")
print(data)
