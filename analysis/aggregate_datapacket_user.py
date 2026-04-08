import msgpack  # type: ignore
import pandas as pd  # type: ignore
from pathlib import Path


def load_all_simulations(base_logs_path):
    all_data = []
    base_dir = Path(base_logs_path)

    packet_files = list(base_dir.rglob("DataPacket.msgpack"))

    if not packet_files:
        print(f"Nessun file trovato in {base_logs_path}")
        return pd.DataFrame()

    for file_path in packet_files:

        run_id = file_path.parent.name  # run_0
        app_name = file_path.parent.parent.name  # 1MMM
        scenario = file_path.parent.parent.parent.name  # 1_26_solution_v0
        distribution = file_path.parent.parent.parent.parent.name  # exponential

        u_file = file_path.parent / "User.msgpack"

        if u_file.exists():
            with open(file_path, "rb") as f:
                df_p = pd.DataFrame(msgpack.unpackb(f.read(), strict_map_key=False))

            with open(u_file, "rb") as f:
                df_u = pd.DataFrame(msgpack.unpackb(f.read(), strict_map_key=False))

            df_temp = df_p.merge(df_u, left_on="User", right_on="Instance ID", how="left", suffixes=("", "_user"))

            df_temp["Distribution"] = distribution
            df_temp["Scenario"] = scenario
            df_temp["App_ms"] = app_name
            df_temp["Run"] = run_id

            all_data.append(df_temp)

    return pd.concat(all_data, ignore_index=True)


base_dir = Path(__file__).resolve().parent
path_log = base_dir.parent / "simulation" / "cavia simulation" / "logs"

full_dataset = load_all_simulations(path_log)

print(full_dataset.head())
print(f"\nDistribuzioni caricate: {full_dataset['Distribution'].unique()}")

Path("analysis/processed_data").mkdir(parents=True, exist_ok=True)
full_dataset.to_pickle("analysis/processed_data/dataset_raw_datpacket_user.pkl")
