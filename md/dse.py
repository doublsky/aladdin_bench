"""
Sweep md
"""

import subprocess as sp
import os
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)

summary_filename = "md_summary"
dse_filename = "md_dse.txt"

dse_df = pd.DataFrame()
for num_atoms in [16]:
    for num_simd_lanes in [1]:
        for cycle_time in range(1, 2):
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
                sep=":\s*",
                skiprows=3,
                skipfooter=3,
                engine="python",
                index_col=0
            )
            summary.set_index("param")
            summary = summary.transpose()
            summary["num_atoms"] = num_atoms
            summary["num_simd_lanes"] = num_simd_lanes
            summary["cycle_time"] = cycle_time
            logging.debug(summary)
            dse_df = dse_df.append(summary)
            logging.debug(dse_df)

dse_df.to_csv(dse_filename)
