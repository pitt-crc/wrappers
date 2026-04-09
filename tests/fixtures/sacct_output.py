"""Fixtures for `sacctmgr` and `sacct` output.

Used by the `Slurm` utility class methods (`get_cluster_names`,
`get_partition_names``, ``check_slurm_account_exists``,
``get_cluster_usage_by_user``, ``is_installed``).
"""

# ---------------------------------------------------------------------------
# sacctmgr / scontrol — cluster names
# ---------------------------------------------------------------------------

# Normal multi-cluster output; "azure" is a known ignored cluster
CLUSTER_NAMES = "CLUSTER: smp\nCLUSTER: gpu\nCLUSTER: mpi\nCLUSTER: htc\nCLUSTER: azure\n"

# Single cluster
CLUSTER_NAMES_SINGLE = "CLUSTER: smp\n"

# Empty — no clusters configured
CLUSTER_NAMES_EMPTY = ""

# ---------------------------------------------------------------------------
# scontrol show partition — partition names
# ---------------------------------------------------------------------------

# Normal output with an ignored (personal) partition
PARTITION_NAMES = (
    "PartitionName=smp\n"
    "PartitionName=high-mem\n"
    "PartitionName=pliu\n"  # personal/ignored partition
)

# Single partition
PARTITION_NAMES_SINGLE = "PartitionName=smp\n"

# Empty — no partitions configured
PARTITION_NAMES_EMPTY = ""

# ---------------------------------------------------------------------------
# sacctmgr — account existence check
# ---------------------------------------------------------------------------

# Account found
ACCOUNT_EXISTS = "mygroup"

# Account not found (empty output)
ACCOUNT_NOT_FOUND = ""

# ---------------------------------------------------------------------------
# sacct — per-user cluster usage
# ---------------------------------------------------------------------------

# Format: user|cpu_seconds  (last row has empty user = group total)
USAGE_MULTI_USER = "user1|100\nuser2|200\n|300"

# Single user
USAGE_SINGLE_USER = "user1|500\n|500"

# No usage recorded yet
USAGE_EMPTY = ""

# ---------------------------------------------------------------------------
# sacctmgr version string — used by is_installed()
# ---------------------------------------------------------------------------

VERSION_STRING = "slurm 22.05.11"
