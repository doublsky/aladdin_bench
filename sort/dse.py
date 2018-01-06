"""
Sweep gemm
"""

import subprocess as sp
import os
import pandas as pd

dse_filename = "ss_sort_dse.csv"
summary_filename = "ss_sort_summary"


def calc_energy(df):
    num_df = df.apply(pd.to_numeric, errors="ignore")
    total_energy = num_df["Avg Power (mW)"] * num_df["Cycle (cycles)"] * num_df["Cycle Time (ns)"]
    total_input_bits = 2048 * 32 + 2048 * 32 + 32
    total_output_bits = 2048 * 32
    num_df["Energy per Input (pJ/bit)"] = total_energy / total_input_bits
    num_df["Energy per Output (pJ/bit)"] = total_energy / total_output_bits
    num_df.to_csv(dse_filename, index=False)

if __name__ == "__main__":
    dse_df = pd.DataFrame()
    for num_simd_lanes in range(1, 2):
        for cycle_time in range(1, 2):
            # compile with different num_atoms
            sp.check_call(["make", "run-trace"])

            # get path to aladdin
            aladdin_home = os.environ["ALADDION_HOME"]
            if not aladdin_home:
                raise Exception("ALADDION_HOME not defined")

            # create config file
            config_content = "partition,cyclic,a,8192,4,{}\n".format(num_simd_lanes)
            config_content += "partition,cyclic,b,8192,4,{}\n".format(num_simd_lanes)
            config_content += "partition,cyclic,bucket,8193,4,{}\n".format(num_simd_lanes)
            config_content += "partition,cyclic,sum,512,4,{}\n".format(num_simd_lanes)
            config_content += "unrolling,init,loop1_outer,{}\n".format(num_simd_lanes)
            config_content += "unrolling,hist,loop1,{}\n".format(min(num_simd_lanes, 4))
            config_content += "unrolling,hist,loop2,{}\n".format((num_simd_lanes+4-1)//4)
            config_content += "flatten,local_scan,23"
            config_content += "flatten,last_step_scan,44"
            config_content += "unrolling,update,loop1,{}\n".format(min(num_simd_lanes, 4))
            config_content += "unrolling,update,loop3,{}\n".format((num_simd_lanes + 4 - 1) // 4)
            config_content += "pipelining,1\n"
            config_content += "cycle_time,{}\n".format(cycle_time)

            with open("config", "w") as f:
                f.write(config_content)

            aladdin_bin = os.path.join(aladdin_home, "common/aladdin")
            aladdin_cmd = [aladdin_bin, "ss_sort", "dynamic_trace.gz", "config"]
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
            summary["Num of SIMD Lanes"] = num_simd_lanes
            summary["Cycle Time (ns)"] = cycle_time
            dse_df = dse_df.append(summary)
            calc_energy(dse_df)
