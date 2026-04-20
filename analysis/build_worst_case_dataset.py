from adapters.cavia.utils.path import BASE_PATH
import msgpack  # type: ignore
import pandas as pd  # type: ignore
from pathlib import Path

LOGS_PATH = BASE_PATH / "simulation" / "cavia_simulation" / "logs"


def build_worst_case_dataset(base_logs_path):
    results = []
    base_dir = Path(base_logs_path)

    packet_files = list(base_dir.rglob("DataPacket.msgpack"))

    if not packet_files:
        print(f"No file found in {base_logs_path}")
        return pd.DataFrame()

    for packet_file in packet_files:

        run_id = packet_file.parent.name
        app_name = packet_file.parent.parent.name
        scenario = packet_file.parent.parent.parent.name
        distribution = packet_file.parent.parent.parent.parent.name

        user_file = packet_file.parent / "User.msgpack"

        if not user_file.exists():
            raise FileNotFoundError(f"Missing user file: {user_file}")

        with open(packet_file, "rb") as f:
            df_p = pd.DataFrame(msgpack.unpackb(f.read(), strict_map_key=False))

        df = df_p[df_p["Status"] == "finished"].copy()

        if df.empty:
            raise ValueError(f"No finished DataPacket found in {packet_file}")

        with open(user_file, "rb") as f:
            df_u = pd.DataFrame(msgpack.unpackb(f.read(), strict_map_key=False))

        sla = list(df_u["Delay SLAs"].dropna().iloc[0].values())[0]

        # df = df_p.merge(df_u[["Instance ID", "Time Step"]], left_on=["User", "Time Step"], right_on=["Instance ID", "Time Step"], how="left")

        df["Distribution"] = distribution
        df["Scenario"] = scenario
        df["App_ms"] = app_name
        df["Run"] = run_id
        df["Delay SLAs"] = sla

        idx = df["Total Delay"].idxmax()
        worst = df.loc[idx].copy()

        worst["SLA_Violation"] = worst["Total Delay"] > worst["Delay SLAs"]
        worst["SLA_Margin"] = worst["Total Delay"] - worst["Delay SLAs"]
        worst["SLA_Margin_Perc"] = round((worst["SLA_Margin"] / worst["Delay SLAs"]) * 100, 3)
        worst["Violation_Amount"] = max(0, worst["SLA_Margin"])

        worst = worst[
            [
                "Distribution",
                "Scenario",
                "App_ms",
                "Run",
                "User",
                "Application",
                "Total Delay",
                "Delay SLAs",
                "SLA_Violation",
                "SLA_Margin",
                "SLA_Margin_Perc",
                "Violation_Amount",
                "Processing Delay",
                "Propagation Delay",
            ]
        ]

        results.append(worst)

    df_final = pd.DataFrame(results).reset_index(drop=True)

    dup_mask = df_final.duplicated(subset=["Distribution", "Scenario", "App_ms", "Run"], keep=False)

    if dup_mask.any():
        raise ValueError(f"Duplicate worst-case rows found: {dup_mask.sum()}")

    return df_final


if __name__ == "__main__":
    print("Building dataset of worst case scenarios...")

    datapacket_user_dataset = build_worst_case_dataset(LOGS_PATH)

    print(datapacket_user_dataset.head())
    print(f"\nLoaded distributions: {datapacket_user_dataset['Distribution'].unique()}")

    Path("analysis/processed_data").mkdir(parents=True, exist_ok=True)
    datapacket_user_dataset.to_pickle("analysis/processed_data/dataset_worst_case_scenarios.pkl")
