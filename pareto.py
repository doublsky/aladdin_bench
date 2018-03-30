"""
calculate pareto frontier
"""

import pandas as pd

sheet_name = "sort"
pareto_filename = "/tmp/tmp_pareto.csv"
key = ["N"]


def find_pareto_frontier(df):
    pareto_df = pd.DataFrame()
    for df_index, df_row in df.iterrows():
        # assume pareto optimal
        is_pareto_optimal = True

        candidate_exe_time = df_row["Cycle (cycles)"] * df_row["Cycle Time (ns)"]
        candidate_area = df_row["Total Area (uM^2)"]
        candidate_energy = df_row["Energy per Input (pJ/bit)"]

        # check optimality
        for pareto_index, pareto_row in pareto_df.iterrows():
            pareto_exe_time = pareto_row["Cycle (cycles)"] * pareto_row["Cycle Time (ns)"]
            pareto_area = pareto_row["Total Area (uM^2)"]
            pareto_energy = pareto_row["Energy per Input (pJ/bit)"]
            if candidate_exe_time >= pareto_exe_time \
                    and candidate_energy >= pareto_energy \
                    and candidate_area >= pareto_area:
                is_pareto_optimal = False
                break
            if candidate_exe_time <= pareto_exe_time \
                    and candidate_energy <= pareto_energy \
                    and candidate_area <= pareto_area:
                pareto_df = pareto_df.drop(pareto_index)

        # add if pareto optimal
        if is_pareto_optimal:
            pareto_df = pareto_df.append(df_row)

    return pareto_df


if __name__ == "__main__":
    df = pd.read_excel("/Users/doublsky/OneDrive/FPGAvsASIC/aladdin.xlsx", sheet_name=sheet_name, index_col=None)
    column_order = df.columns.tolist()
    print "Raw Data Size:", df.shape
    grouped_df = df.groupby(key)
    result_df = pd.DataFrame()

    for name, group in grouped_df:
        pareto_frontier = find_pareto_frontier(group)
        result_df = result_df.append(pareto_frontier, ignore_index=True)

    print "Pareto Date Size:", result_df.shape
    result_df.to_csv(pareto_filename, columns=column_order, index=False)
