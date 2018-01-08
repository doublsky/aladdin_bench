"""
calculate pareto frontier
"""

import pandas as pd

csv_filename = "md/md_dse.csv"
key1 = "Num of Atoms"
key2 = "Cycle Time (ns)"


def find_pareto_frontier(df):
    pareto_df = pd.DataFrame()
    for df_index, df_row in df.iterrows():
        for pareto_index, pareto_row in pareto_df.iterrows():
            is_pareto_optimal = False
            if df_row["Cycle (cycles)"] > pareto_row["Cycle (cycles)"] \
                    and df_row["Avg Power (mW)"] > pareto_row["Avg Power (mW)"] \
                    and df_row["Total Area (uM^2)"] > pareto_row["Total Area (uM^2)"]:
                break
            if df_row["Cycle (cycles)"] < pareto_row["Cycle (cycles)"] \
                    and df_row["Avg Power (mW)"] < pareto_row["Avg Power (mW)"] \
                    and df_row["Total Area (uM^2)"] < pareto_row["Total Area (uM^2)"]:
                pareto_df = pareto_df.drop(pareto_index)
                is_pareto_optimal = True
            if is_pareto_optimal:
                pareto_df = pareto_df.append(pareto_row)
    return pareto_df


if __name__ == "__main__":
    df = pd.read_csv(csv_filename)
    grouped_df = df.groupby([key1, key2])
    result_df = pd.DataFrame()

    for name, group in grouped_df:
        pareto_frontier = find_pareto_frontier(group)
        result_df = result_df.append(pareto_frontier)
