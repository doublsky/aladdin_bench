"""
Sweep kmp
"""

import subprocess as sp
import os
import pandas as pd
import numpy as np

dse_filename = "kmp_dse.csv"
summary_filename = "kmp_summary"


def calc_energy(df):
    num_df = df.apply(pd.to_numeric, errors="ignore")
    total_energy = num_df["Avg Power (mW)"] * num_df["Cycle (cycles)"] * num_df["Cycle Time (ns)"]
    total_input_bits = num_df["STRING_SIZE"] * 32 * 2
    total_output_bits = num_df["STRING_SIZE"] * 32 * 2
    num_df["Energy per Input (pJ/bit)"] = total_energy / total_input_bits
    num_df["Energy per Output (pJ/bit)"] = total_energy / total_output_bits
    num_df.to_csv(dse_filename, index=False)

if __name__ == "__main__":
    dse_df = pd.DataFrame()
    for string_size in [2048, 4096]:
        for num_simd_lanes in [2**i for i in range(2)]:
            for cycle_time in range(1, 2) + [10]:
                # clean
                sp.check_call(["make", "clean-trace"])
                sp.check_call(["make", "clean"])
                
                # compile
                make_cmd = [
                    "make",
                    "MACROS=-DSTRING_SIZE={}".format(string_size),
                    "generate"
                ]
                sp.check_call(make_cmd)

                # compile
                make_cmd = [
                    "make",
                    "MACROS=-DSTRING_SIZE={}".format(string_size),
                    "run-trace"
                ]
                sp.check_call(make_cmd)

                # get path to aladdin
                aladdin_home = os.environ["ALADDIN_HOME"]
                if not aladdin_home:
                    raise Exception("ALADDIN_HOME not defined")

                # create config file
                config_content = "partition,complete,pattern,4\n"
                config_content += "partition,cyclic,imput,{},1,{}\n".format(string_size, num_simd_lanes)
                config_content += "partition,complete,kmpNext,16\n"
                config_content += "partition,complete,n_matches,4\n"
                config_content += "unrolling,kmp,k1,{}\n".format(num_simd_lanes)
                config_content += "pipelining,1\n"
                config_content += "cycle_time,{}\n".format(cycle_time)

                with open("config", "w") as f:
                    f.write(config_content)

                aladdin_bin = os.path.join(aladdin_home, "common/aladdin")
                aladdin_cmd = [aladdin_bin, "kmp", "dynamic_trace.gz", "config"]
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
                summary["STRING_SIZE"] = string_size
                summary["Num of SIMD Lanes"] = num_simd_lanes
                summary["Cycle Time (ns)"] = cycle_time
                dse_df = dse_df.append(summary)
                calc_energy(dse_df)
