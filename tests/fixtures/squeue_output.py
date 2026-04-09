"""Fixtures for `squeue` output.

These strings are representative of real Slurm squeue output. They serve as
the single source of truth for all tests that mock `Shell.run_command` for
squeue calls.

Columns (user format): JOBID, PARTITION, NAME, ST, TIME, NODES, CPUS, NODELIST(REASON), START_TIME
Columns (all format):  JOBID, PARTITION, ACCOUNT, USER, NAME, ST, TIME, NODES, CPUS, NODELIST(REASON), START_TIME
"""

# --- User-scoped output (default, single user) ---

# One running job
SINGLE_JOB_RUNNING = (
    "   12345 smp      my_job           R     1:23:45      1    4 node01           2024-01-15T08:00:00"
)

# One pending job
SINGLE_JOB_PENDING = (
    "   12346 gpu      gpu_job          PD     0:00:00      1    2 (Resources)      N/A"
)

# Mixed running and pending
MIXED_RUNNING_PENDING = (
    "   12345 smp      my_job           R     1:23:45      1    4 node01           2024-01-15T08:00:00\n"
    "   12346 gpu      gpu_job          PD     0:00:00      1    2 (Resources)      N/A"
)

# No jobs queued
EMPTY = ""

# --- All-users output ---

ALL_USERS_JOBS = (
    "   12345 smp      acct1  user1  job_a      R     1:23:45      1    4 node01  2024-01-15T08:00:00\n"
    "   12346 gpu      acct2  user2  job_b      PD     0:00:00      1    2 (Resources)  N/A"
)
