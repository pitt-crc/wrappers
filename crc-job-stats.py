#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
from subprocess import Popen, PIPE
from os import environ


def print_item(name):
    print("{:>16s}: {}".format(name, job_info[name]))


if "SLURM_JOB_ID" in environ:
    # Get the output
    process = Popen(['scontrol', '-M', environ['SLURM_CLUSTER_NAME'], 'show', 'job', environ['SLURM_JOB_ID']], stdout=PIPE, stderr=PIPE)
    output, error = process.communicate()

    # Split the output, turn it into a dictionary
    split_output = output.strip().split()

    # Need to deal with spaces in directory names
    drop_indices = []
    for idx, item in enumerate(split_output):
        if "=" not in item:
            drop_indices.append(idx)
            split_output[idx - 1] += "\ " + item
    for drop_idx in reversed(sorted(drop_indices)):
        del split_output[drop_idx]

    # Extract the job information
    job_info = {}
    for item in split_output:
        spl = item.split('=', 1)
        job_info[spl[0]] = spl[1]

    # Begin Wrapper
    width = 76
    print('=' * width)
    print("JOB STATISTICS".center(75))
    print('=' * width)

    # Print it all out
    for item in ["SubmitTime", "EndTime", "RunTime", "JobId", "TRES", "Partition", "NodeList", "Command", "StdOut"]:
         #if item == "Gres":
         #    if job_info[item] != "(null)":
         #       print_item(item)
         #else:
            print_item(item)

    print("More information:")
    print("    - `sacct -M {} -j {} -S {} -E {}`".format(environ['SLURM_CLUSTER_NAME'], job_info["JobId"], job_info["SubmitTime"], job_info["EndTime"]))
    print("{:>17s}".format("Print control:"))
    print("    - List of all possible fields: `sacct --helpformat`")
    print("    - Add `--format=<field1,field2,etc>` with fields of interest")

    # End Wrapper
    print('=' * width)
else:
    print("Error: This script is meant to be added at the bottom of your Slurm scripts!")
