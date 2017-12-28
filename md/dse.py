"""
Sweep md
"""

import subprocess as sp
import os
import pandas as pd
import logging

#logging.basicConfig(level=logging.DEBUG)

summary_filename = "md_summary"
dse_filename = "md_dse.csv"

dse_df = pd.DataFrame()
for num_atoms in [16]:
    for num_simd_lanes in [1]:
        for cycle_time in range(1, 3):
            # compile with different num_atoms
            make_cmd = [
                "make",
                'CPPFLAGS="-DnAtoms={} -DmaxNeighbors={}"'.format(num_atoms, num_atoms),
                "run-trace"
            ]
            sp.check_call(make_cmd)

            # get path to aladdin
            aladdin_home = os.environ["ALADDION_HOME"]
            if not aladdin_home:
                raise Exception("ALADDION_HOME not defined")

            # create config file
            config_content = "partition,cyclic,d_force_x,256,4,1\n"
            config_content += "partition,cyclic,d_force_y,256,4,1\n"
            config_content += "partition,cyclic,d_force_z,256,4,1\n"
            config_content += "partition,cyclic,position_x,256,4,{}\n".format(num_simd_lanes)
            config_content += "partition,cyclic,position_y,256,4,{}\n".format(num_simd_lanes)
            config_content += "partition,cyclic,position_z,256,4,{}\n".format(num_simd_lanes)
            config_content += "partition,cyclic,NL,16384,4,{}\n".format(num_simd_lanes)
            config_content += "unrolling,md,loop_j,{}\n".format(num_simd_lanes)
            config_content += "pipelining,1\n"
            config_content += "cycle_time,{}\n".format(cycle_time)

            with open("config", "w") as f:
                f.write(config_content)

            aladdin_bin = os.path.join(aladdin_home, "common/aladdin")
            aladdin_cmd = [aladdin_bin, "md", "dynamic_trace.gz", "config"]
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
            summary["Num of Atoms"] = num_atoms
            summary["Num of SIMD Lanes"] = num_simd_lanes
            summary["Cycle Time (ns)"] = cycle_time
            logging.debug(summary)
            dse_df = dse_df.append(summary)
            logging.debug(dse_df)

# calculate energy per bit

total_energy = dse_df["Avg Power (mW)"].apply(pd.to_numeric) * dse_df["Cycle (cycles)"].apply(pd.to_numeric) * \
               dse_df["Cycle Time (ns)"].apply(pd.to_numeric)
total_input_bits = dse_df["Num of Atoms"] * 3 * 32 + dse_df["Num of Atoms"] * dse_df["Num of Atoms"] * 32
total_output_bits = dse_df["Num of Atoms"] * 3 * 32
dse_df["Energy per Input (pJ/bit)"] = total_energy / total_input_bits
dse_df["Energy per Output (pJ/bit)"] = total_energy / total_output_bits
dse_df.to_csv(dse_filename, index=False)
