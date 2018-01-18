"""
calculate pareto frontier
"""

import pandas as pd

csv_filename = "md/md_dse.csv"
pareto_filename = "md/md_pareto.csv"
key1 = "Num of Atoms"
key2 = "Cycle Time (ns)"


def find_pareto_frontier(df):
    pareto_df = pd.DataFrame()
    for df_index, df_row in df.iterrows():
        # assume pareto optimal
        is_pareto_optimal = True

        # check optimality
        for pareto_index, pareto_row in pareto_df.iterrows():
            if df_row["Cycle (cycles)"] >= pareto_row["Cycle (cycles)"] \
                    and df_row["Energy per Input (pJ/bit)"] >= pareto_row["Energy per Input (pJ/bit)"] \
                    and df_row["Total Area (uM^2)"] >= pareto_row["Total Area (uM^2)"]:
                is_pareto_optimal = False
                break
            if df_row["Cycle (cycles)"] <= pareto_row["Cycle (cycles)"] \
                    and df_row["Energy per Input (pJ/bit)"] <= pareto_row["Energy per Input (pJ/bit)"] \
                    and df_row["Total Area (uM^2)"] <= pareto_row["Total Area (uM^2)"]:
                pareto_df = pareto_df.drop(pareto_index)

        # add if pareto optimal
        if is_pareto_optimal:
            pareto_df = pareto_df.append(df_row)

    return pareto_df


if __name__ == "__main__":
    df = pd.read_csv(csv_filename, index_col=None)
    column_order = df.columns.tolist()
    print "Raw Data Size:", df.shape
    grouped_df = df.groupby([key1, key2])
    result_df = pd.DataFrame()

    for name, group in grouped_df:
        pareto_frontier = find_pareto_frontier(group)
        result_df = result_df.append(pareto_frontier, ignore_index=True)

    print "Pareto Date Size:", result_df.shape
    result_df.to_csv(pareto_filename, columns=column_order, index=False)
