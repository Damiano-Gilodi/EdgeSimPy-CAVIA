import os
import pickle
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

HOME_DIR = os.path.expanduser("~")
PKL_BASE_PATH = os.path.join(HOME_DIR, "Desktop", "CAVIA", "src", "LR")

pkl_path = os.path.join(PKL_BASE_PATH, "1_26_solution_v1/var_coeff_values_1MMM_slss.pkl")


with open(pkl_path, "rb") as f:
    data = pickle.load(f)

print("\nKeys:")
for k in data.keys():
    print(" -", k)

print("\nFull object preview:")
# print(data)

# print("map_k_ui:", data["map_k_ui"])
# print("map_k_ui_end:", data["map_k_ui_end"])

# print("ms_map:", data["ms_map"])
# print("Amap:", data["Amap"])

print("latency_limit:", data["latency_limit"])

print("status:", data["status"])

print("sol_count:", data["sol_count"])

# file slss.pkl
# print("x_ui:", data["x_ui"])
x_ui = data.get("x_ui", {})
x_ui_active = {k: v for k, v in x_ui.items() if v > 0.5}
print("\nx_ui_active:", x_ui_active)

# file lrslss.pkl
y_e_ij = data.get("y_e_ij", {})
y_e_ij_active = {k: v for k, v in y_e_ij.items() if v > 0.5}
print("\ny_e_ij_active:", y_e_ij_active)
