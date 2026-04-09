"""Fixtures for `sinfo -N -o %N,%C,%e,%t` output (CPU clusters).

Format per line: NodeName,allocated/idle/other/total,free_mem_MB,state

These strings are representative of real Slurm output. They serve as the
single source of truth for all tests that mock `Shell.run_command` for
CPU-cluster sinfo calls. If the real command's output format ever changes,
update here and all downstream tests will reflect it automatically.
"""

# --- Normal / healthy nodes ---

# Two nodes: one with 4 idle cores / 3500 MB free, one with 2 idle cores / 4000 MB free
MIXED_HEALTHY = "node1,2/4/0/6,3500,mix\nnode2,4/2/0/6,4000,mix"

# All cores idle on a single node
FULLY_IDLE = "node1,0/8/0/8,16000,idle"

# All cores allocated, no free cores
FULLY_ALLOCATED = "node1,8/0/0/8,1024,alloc"

# Multiple nodes with the same idle count (tests count aggregation)
MULTIPLE_NODES_SAME_IDLE = (
    "node1,2/4/0/6,3000,mix\n"
    "node2,2/4/0/6,3500,mix\n"
    "node3,2/4/0/6,4000,mix"
)

# Free memory reported as N/A (VAST / certain configurations)
FREE_MEM_NOT_AVAILABLE = "node1,0/8/0/8,N/A,idle"

# --- Downed / drained nodes ---

# Single down node
SINGLE_DOWN = "node1,2/4/0/6,3500,down*"

# Single drained node
SINGLE_DRAIN = "node1,2/4/0/6,3500,drain*"

# Mixed: one healthy, one down, one drained
MIXED_DOWN_AND_DRAIN = (
    "node1,2/4/0/6,3500,mix\n"
    "node2,2/4/0/6,4000,down*\n"
    "node3,2/4/0/6,4500,drain*"
)

# All nodes downed
ALL_DOWN = "node1,2/4/0/6,3500,down*\nnode2,2/4/0/6,4000,down*"

# Empty output — partition exists but has no nodes
EMPTY = ""
