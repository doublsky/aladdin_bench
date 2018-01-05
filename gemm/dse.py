"""
Sweep gemm
"""

import subprocess as sp
import os
import pandas as pd

dse_filename = "bb_gemm_dse.csv"
summary_filename = "bb_gemm_summary"


def calc_energy(df):
    num_df = df.apply(pd.to_numeric, errors="ignore")
    total_energy = num_df["Avg Power (mW)"] * num_df["Cycle (cycles)"] * num_df["Cycle Time (ns)"]
    total_input_bits = num_df["Row Size"] * num_df["Block Size"] * 32 \
                       + num_df["Block Size"] * num_df["Block Size"] * 32 \
                       + num_df["Row Size"] * num_df["Block Size"] * 32
    total_output_bits = num_df["Row Size"] * num_df["Block Size"] * 32
    num_df["Energy per Input (pJ/bit)"] = total_energy / total_input_bits
    num_df["Energy per Output (pJ/bit)"] = total_energy / total_output_bits
    num_df.to_csv(dse_filename, index=False)

if __name__ == "__main__":
    dse_df = pd.DataFrame()
    for block_size in [8]:
        for num_simd_lanes in range(1, 5):
            for cycle_time in range(1, 2):
                # clean
                sp.check_call(["make", "clean-trace"])

                # compile with different num_atoms
                make_cmd = [
                    "make",
                    "CPPFLAGS=-DBLOCKSIZE={}".format(block_size),
                    "run-trace"
                ]
                sp.check_call(make_cmd)

                # get path to aladdin
                aladdin_home = os.environ["ALADDION_HOME"]
                if not aladdin_home:
                    raise Exception("ALADDION_HOME not defined")

                # create config file
                config_content = "partition,cyclic,x,{},4,{}\n".format(block_size * block_size * 4, num_simd_lanes)
                config_content += "partition,cyclic,y,{},4,{}\n".format(block_size * block_size * 4, num_simd_lanes)
                config_content += "partition,cyclic,z,{},4,{}\n".format(block_size * block_size * 4, num_simd_lanes)
                config_content += "unrolling,bb_gemm,loopj,{}\n".format(num_simd_lanes)
                config_content += "pipelining,1\n"
                config_content += "cycle_time,{}\n".format(cycle_time)

                with open("config", "w") as f:
                    f.write(config_content)

                aladdin_bin = os.path.join(aladdin_home, "common/aladdin")
                aladdin_cmd = [aladdin_bin, "bb_gemm", "dynamic_trace.gz", "config"]
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
                summary["Row Size"] = block_size
                summary["Block Size"] = block_size
                summary["Num of SIMD Lanes"] = num_simd_lanes
                summary["Cycle Time (ns)"] = cycle_time
                dse_df = dse_df.append(summary)
                calc_energy(dse_df)
