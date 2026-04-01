import os
import pickle

from adapters.cavia.utils.path import PKL_PATH

pkl_path = os.path.join(PKL_PATH, "2_26_solution_v107/var_coeff_values_2SMM_slss.pkl")


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
