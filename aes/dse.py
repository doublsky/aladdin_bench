"""
Sweep aes
"""

import subprocess as sp
import os
import pandas as pd

dse_filename = "aes256_encrypt_ecb_dse.csv"
summary_filename = "aes256_encrypt_ecb_summary"


def calc_energy(df):
    num_df = df.apply(pd.to_numeric, errors="ignore")
    total_energy = num_df["Avg Power (mW)"] * num_df["Cycle (cycles)"] * num_df["Cycle Time (ns)"]
    total_input_bits = (32+16) * 8
    total_output_bits = 16 * 8
    num_df["Energy per Input (pJ/bit)"] = total_energy / total_input_bits
    num_df["Energy per Output (pJ/bit)"] = total_energy / total_output_bits
    num_df.to_csv(dse_filename, index=False)

if __name__ == "__main__":
    dse_df = pd.DataFrame()
    for num_simd_lanes in range(1, 14):
        for cycle_time in range(1, 7):
            # compile
            sp.check_call(["make", "run-trace"])

            # get path to aladdin
            aladdin_home = os.environ["ALADDIN_HOME"]
            if not aladdin_home:
                raise Exception("ALADDIN_HOME not defined")

            # create config file
            ## args
            config_content = "partition,complete,k,32\n"
            config_content += "partition,complete,buf,16\n"
            config_content += "partition,complete,ctx,96\n"
            
            ## ecb1
            config_content += "flatten,aes256_encrypt_ecb,192\n"
            
            ## aes_addRoundKey_cpy
            config_content += "flatten,aes_addRoundKey_cpy,126\n"
            
            ## ecb3
            config_content += "unrolling,aes256_encrypt_ecb,ecb3,{}\n".format(num_simd_lanes)
            
            ## aes_subBytes
            config_content += "flatten,aes_subBytes,110\n"
            config_content += "partition,cyclic,sbox,256,1,{}".format(num_simd_lanes * 16)
            
            ## aes_mixColumns
            config_content += "flatten,aes_mixColumns,147\n"
            
            ## aes_addRoundKey
            config_content += "flatten,aes_addRoundKey,118\n"
            
            ## aes_expandEncKey
            config_content += "flatten,aes_expandEncKey,167\n"
            config_content += "flatten,aes_expandEncKey,174\n"
            
            ## others
            config_content += "pipelining,1\n"
            config_content += "cycle_time,{}\n".format(cycle_time)

            with open("config", "w") as f:
                f.write(config_content)

            aladdin_bin = os.path.join(aladdin_home, "common/aladdin")
            aladdin_cmd = [aladdin_bin, "aes256_encrypt_ecb", "dynamic_trace.gz", "config"]
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
