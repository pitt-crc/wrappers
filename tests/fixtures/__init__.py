"""Test fixtures for Slurm command output.

Each sub-module contains string constants representing real Slurm command
output for a specific command. Tests should import from here rather than
defining inline mock strings, so that any format change only needs to be
updated in one place.

Sub-modules
-----------
sinfo_cpu_nodes  -- `sinfo -N -o %N,%C,%e,%t` output for CPU clusters
sinfo_gpu_nodes  -- `sinfo -N --Format=...` output for GPU clusters
squeue_output    -- `squeue` output for user and all-user views
scontrol_output  -- `scontrol show partition/node/job/hostname` output
sacct_output     -- `sacctmgr` and `sacct` output
"""

from . import (
    sinfo_cpu_nodes,
    sinfo_gpu_nodes,
    squeue_output,
    scontrol_output,
    sacct_output,
)

__all__ = [
    'sinfo_cpu_nodes',
    'sinfo_gpu_nodes',
    'squeue_output',
    'scontrol_output',
    'sacct_output',
]
