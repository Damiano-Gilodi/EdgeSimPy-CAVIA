from pathlib import Path
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
import networkx as nx  # type: ignore
import msgpack  # type: ignore


BASE_DIR = Path(__file__).resolve().parent
LOGS_PATH = BASE_DIR.parent / "simulation" / "cavia_simulation" / "logs"

CAVIA_BASE_PATH = BASE_DIR.parents[1] / "CAVIA" / "src" / "SIMPY"

OUTPUT_DIR = BASE_DIR / "processed_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "service_cavia_mean.pkl"


def load_cavia_means_for_app(app_graph_path, skip_special_nodes=False):
    if not app_graph_path.exists():
        raise FileNotFoundError(f"GraphML not found: {app_graph_path}")

    G = nx.read_graphml(app_graph_path)

    rows = []
    for node_id, data in G.nodes(data=True):
        service_id = int(node_id)
        node_type = data.get("node_type", "")
        cavia_mean = float(data.get("4", 0))

        if skip_special_nodes and node_type in {"input", "destination"}:
            continue

        rows.append(
            {
                "Service_ID": service_id,
                "Node_Type": node_type,
                "Cavia_Mean": cavia_mean,
            }
        )

    return pd.DataFrame(rows)


def build_consistency_dataset(base_logs_path, cavia_base_path, skip_special_nodes=False):
    all_data = []
    base_dir = Path(base_logs_path)

    service_files = list(base_dir.rglob("Service.msgpack"))

    if not service_files:
        print(f"No Service.msgpack file found in {base_logs_path}")
        return pd.DataFrame()

    for file_path in service_files:
        try:
            run_id = file_path.parent.name
            app_name = file_path.parent.parent.name
            scenario = file_path.parent.parent.parent.name
            distribution = file_path.parent.parent.parent.parent.name

            with open(file_path, "rb") as f:
                df_s = pd.DataFrame(msgpack.unpackb(f.read(), strict_map_key=False))

            df_s = df_s[df_s["Time Step"] == 0].copy()

            df_s = df_s[["Instance ID", "Processing Time"]].copy()
            df_s.rename(columns={"Instance ID": "Service_ID", "Processing Time": "Processing_Time"}, inplace=True)

            df_s["Service_ID"] = df_s["Service_ID"].astype(int)
            df_s["Processing_Time"] = pd.to_numeric(df_s["Processing_Time"], errors="coerce")

            app_graph_path = Path(cavia_base_path) / scenario / "ms" / f"{app_name}.graphml"
            df_cavia = load_cavia_means_for_app(app_graph_path=app_graph_path, skip_special_nodes=skip_special_nodes)

            df_temp = df_s.merge(df_cavia, on="Service_ID", how="left")
            df_temp["Distribution"] = distribution
            df_temp["Scenario"] = scenario
            df_temp["App_ms"] = app_name
            df_temp["Run"] = run_id

            all_data.append(df_temp)

        except Exception as e:
            print(f"Error during reading {file_path}: {e}")

    raw_df = pd.concat(all_data, ignore_index=True)

    consistency_df = (
        raw_df.groupby(["Distribution", "Scenario", "App_ms", "Service_ID", "Node_Type", "Cavia_Mean"], dropna=False)
        .agg(
            Num_Runs=("Run", "count"),
            Empirical_Mean=("Processing_Time", "mean"),
            Empirical_Std=("Processing_Time", "std"),
            Empirical_Min=("Processing_Time", "min"),
            Empirical_Max=("Processing_Time", "max"),
        )
        .reset_index()
    )

    consistency_df["Empirical_Std"] = consistency_df["Empirical_Std"].fillna(0.0)
    consistency_df["Abs_Error"] = (consistency_df["Empirical_Mean"] - consistency_df["Cavia_Mean"]).abs()
    consistency_df["Rel_Error_Percent"] = np.where(consistency_df["Cavia_Mean"] != 0, consistency_df["Abs_Error"] / consistency_df["Cavia_Mean"] * 100, 0.0)

    return consistency_df


if __name__ == "__main__":
    print("Building service cavia mean dataset...")

    consistency_df = build_consistency_dataset(base_logs_path=LOGS_PATH, cavia_base_path=CAVIA_BASE_PATH, skip_special_nodes=False)

    if consistency_df.empty:
        print("No data available.")
    else:
        consistency_df.to_pickle(OUTPUT_FILE)

        print(consistency_df.head())

        print("\nQuick statistics:")
        print(f"Total rows: {len(consistency_df)}")
        print(f"Distributions: {consistency_df['Distribution'].nunique()}")
        print(f"Scenarios: {consistency_df['Scenario'].nunique()}")
        print(f"App: {consistency_df[['Scenario', 'App_ms']].drop_duplicates().shape[0]}")
        print(f"Average percentage error: {consistency_df['Rel_Error_Percent'].mean():.2f}")
        print(f"Maximum percentage error: {consistency_df['Rel_Error_Percent'].max():.2f}")
        print(f"Average percentage error per distribution:\n {consistency_df.groupby('Distribution')['Rel_Error_Percent'].mean().round(2)}")
