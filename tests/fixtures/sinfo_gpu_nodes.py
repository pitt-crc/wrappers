"""Fixtures for `sinfo -N --Format=NodeList,gres,gresUsed,StateCompact,FreeMem` output (GPU clusters).

Format per line (underscore-delimited as produced by the custom format string):
  NodeName_totalGPUs_allocatedGPUs_state_free_mem_MB

These strings are representative of real Slurm output. They serve as the
single source of truth for all tests that mock `Shell.run_command` for
GPU-cluster sinfo calls. If the real command's output format ever changes,
update here and all downstream tests will reflect it automatically.
"""

# --- Normal / healthy nodes ---

# Two nodes: one with 2 idle GPUs, one fully allocated
MIXED_HEALTHY = "node1_4_2_idle_3500\nnode2_4_4_alloc_4000"

# All GPUs idle on a single node
FULLY_IDLE = "node1_4_0_idle_8000"

# All GPUs allocated
FULLY_ALLOCATED = "node1_4_4_alloc_2048"

# Multiple nodes with the same idle GPU count (tests count aggregation)
MULTIPLE_NODES_SAME_IDLE = (
    "node1_4_2_idle_3000\n"
    "node2_4_2_idle_3500\n"
    "node3_4_2_idle_4000"
)

# Free memory reported as N/A
FREE_MEM_NOT_AVAILABLE = "node1_4_0_idle_N/A"

# --- Drained nodes ---

# Single drained node; Slurm reports state as "drain*" and memory as N/A
SINGLE_DRAIN = "node1_4_2_drain*_N/A"

# Both drain variants Slurm can emit
MIXED_DRAIN_VARIANTS = "node1_4_2_drain*_N/A\nnode2_4_4_drain_N/A"

# Mixed: one healthy, one drained
MIXED_HEALTHY_AND_DRAIN = (
    "node1_4_2_idle_3500\n"
    "node2_4_4_drain*_N/A"
)

# All nodes drained
ALL_DRAIN = "node1_4_2_drain*_N/A\nnode2_4_4_drain_N/A"

# Empty output — partition exists but has no nodes
EMPTY = ""
