"""
Sweep triad
"""

import subprocess as sp
import os
import pandas as pd
import numpy as np

dse_filename = "triad_dse.csv"
summary_filename = "triad_summary"


def calc_energy(df):
    num_df = df.apply(pd.to_numeric, errors="ignore")
    total_energy = num_df["Avg Power (mW)"] * num_df["Cycle (cycles)"] * num_df["Cycle Time (ns)"]
    total_input_bits = num_df["NUM"] * 32 + num_df["NUM"] * 32 + 32
    total_output_bits = num_df["NUM"] * 32
    num_df["Energy per Input (pJ/bit)"] = total_energy / total_input_bits
    num_df["Energy per Output (pJ/bit)"] = total_energy / total_output_bits
    num_df.to_csv(dse_filename, index=False)

if __name__ == "__main__":
    dse_df = pd.DataFrame()
    for num in np.power(2, range(13, 20)):
        for num_simd_lanes in range(1, min(64, num)+1):
            for cycle_time in range(1, 7):
                # clean
                sp.check_call(["make", "clean-trace"])
                
                # compile
                make_cmd = [
                    "make",
                    "MACROS=-DNUM={}".format(num),
                    "run-trace"
                ]
                sp.check_call(make_cmd)

                # get path to aladdin
                aladdin_home = os.environ["ALADDIN_HOME"]
                if not aladdin_home:
                    raise Exception("ALADDIN_HOME not defined")

                # create config file
                config_content = "partition,cyclic,a,{},4,{}\n".format(num * 4, num_simd_lanes)
                config_content += "partition,cyclic,b,{},4,{}\n".format(num * 4, num_simd_lanes)
                config_content += "partition,cyclic,c,{},4,{}\n".format(num * 4, num_simd_lanes)
                config_content += "unrolling,triad,triad,{}\n".format(num_simd_lanes)
                config_content += "pipelining,1\n"
                config_content += "cycle_time,{}\n".format(cycle_time)

                with open("config", "w") as f:
                    f.write(config_content)

                aladdin_bin = os.path.join(aladdin_home, "common/aladdin")
                aladdin_cmd = [aladdin_bin, "triad", "dynamic_trace.gz", "config"]
                sp.check_call(aladdin_cmd)

                # process summary
                summary = pd.read_table(
                    summary_filename,
                    header=None,
                    sep=":\s*",
                    skiprows=3,
                    skipfooter=3,
                    engine="python",
                    index_col=0
                )
                summary = summary.transpose()
                summary["NUM"] = num
                summary["Num of SIMD Lanes"] = num_simd_lanes
                summary["Cycle Time (ns)"] = cycle_time
                dse_df = dse_df.append(summary)
                calc_energy(dse_df)
