def build_sla_summary(df, group_cols):
    if isinstance(group_cols, str):
        group_cols = [group_cols]

    summary = (
        df.groupby(group_cols)
        .agg(
            Runs=("Run", "count"),
            Violations=("SLA_Violation", "sum"),
            Violation_Rate=("SLA_Violation", "mean"),
            Mean_Total_Delay=("Total Delay", "mean"),
            Median_Total_Delay=("Total Delay", "median"),
            Max_Total_Delay=("Total Delay", "max"),
            Mean_SLA_Margin=("SLA_Margin", "mean"),
            Median_SLA_Margin=("SLA_Margin", "median"),
            Min_SLA_Margin=("SLA_Margin", "min"),
            Max_SLA_Margin=("SLA_Margin", "max"),
            Mean_Violation_Amount=("Violation_Amount", "mean"),
            Max_Violation_Amount=("Violation_Amount", "max"),
        )
        .reset_index()
    )

    summary["Violation_Rate"] = summary["Violation_Rate"] * 100

    safe_summary = (
        df[~df["SLA_Violation"]]
        .groupby(group_cols)
        .agg(Mean_Safe_Margin=("SLA_Margin", "mean"), Median_Safe_Margin=("SLA_Margin", "median"), Max_Safe_Margin=("SLA_Margin", "max"))
        .reset_index()
    )

    viol_summary = (
        df[df["SLA_Violation"]]
        .groupby(group_cols)
        .agg(Mean_Violating_Margin=("SLA_Margin", "mean"), Median_Violating_Margin=("SLA_Margin", "median"))
        .reset_index()
    )

    summary = summary.merge(safe_summary, on=group_cols, how="left")
    summary = summary.merge(viol_summary, on=group_cols, how="left")

    return summary.round(3)
