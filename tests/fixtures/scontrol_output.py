"""Fixtures for `scontrol` output.

Used by `crc-show-config` (partition and node info) and `crc-job-stats`
(job info). These strings are representative of real Slurm scontrol output
and serve as the single source of truth for tests that mock `Shell.run_command``
for scontrol calls.
"""

# ---------------------------------------------------------------------------
# scontrol show partition
# ---------------------------------------------------------------------------

SHOW_PARTITION = (
    "PartitionName=smp AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL "
    "AllocNodes=ALL Default=YES QoS=N/A DefaultTime=NONE DisableRootJobs=NO "
    "ExclusiveUser=NO GraceTime=0 Hidden=NO MaxNodes=UNLIMITED MaxTime=UNLIMITED "
    "MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED Nodes=node[01-10] "
    "PriorityJobFactor=1 PriorityTier=1 RootOnly=NO ReqResv=NO OverSubscribe=NO "
    "OverTimeLimit=NONE PreemptMode=OFF State=UP TotalCPUs=320 TotalNodes=10 "
    "SelectTypeParameters=NONE JobDefaults=(null) DefMemPerNode=UNLIMITED "
    "MaxMemPerNode=UNLIMITED"
)

# Partition with a specific node list (used to retrieve a representative node)
SHOW_PARTITION_WITH_NODES = (
    "PartitionName=gpu AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL "
    "AllocNodes=ALL Default=NO QoS=N/A DefaultTime=NONE "
    "Nodes=gpu-node[01-04] State=UP TotalCPUs=128 TotalNodes=4 "
    "SelectTypeParameters=NONE"
)

# ---------------------------------------------------------------------------
# scontrol show node
# ---------------------------------------------------------------------------

SHOW_NODE = (
    "NodeName=node01 Arch=x86_64 CoresPerSocket=16 "
    "CPUAlloc=0 CPUErr=0 CPUTot=32 CPULoad=0.01 "
    "AvailableFeatures=sandybridge "
    "ActiveFeatures=sandybridge "
    "Gres=(null) NodeAddr=node01 NodeHostName=node01 "
    "OS=Linux 4.18.0 "
    "RealMemory=192000 AllocMem=0 FreeMem=185000 Sockets=2 Boards=1 "
    "State=IDLE ThreadsPerCore=2 TmpDisk=0 Weight=1 Owner=N/A MCS_label=N/A "
    "Partitions=smp "
    "BootTime=2024-01-01T00:00:00 SlurmdStartTime=2024-01-01T00:01:00 "
    "CfgTRES=cpu=32,mem=192000M,billing=32 "
    "AllocTRES= "
    "CapWatts=n/a CurrentWatts=0 LowestJoules=0 ConsumedJoules=0 "
    "ExtSensorsJoules=n/s ExtSensorsWatts=0 ExtSensorsTemp=n/s "
    "Reason=Not responding [slurm@2024-01-01T00:00:00]"
)

# ---------------------------------------------------------------------------
# scontrol show job  (used by crc-job-stats)
# ---------------------------------------------------------------------------

SHOW_JOB = (
    "JobId=99999 JobName=my_job "
    "UserId=user1(12345) GroupId=group1(6789) MCS_label=N/A "
    "Priority=1000 Nice=0 Account=myaccount QOS=normal "
    "JobState=RUNNING Reason=None Dependency=(null) "
    "TimeLimit=01:00:00 SubmitTime=2024-01-15T08:00:00 "
    "StartTime=2024-01-15T08:01:00 EndTime=2024-01-15T09:01:00 "
    "RunTime=00:30:00 "
    "NodeList=node01 "
    "BatchHost=node01 "
    "NumNodes=1 NumCPUs=4 NumTasks=4 CPUs/Task=1 "
    "AllocTRES=cpu=4,mem=4G,node=1,billing=4 "
    "Partition=smp "
    "Command=/path/to/my_script.sh "
    "WorkDir=/home/user1 "
    "StdErr=/home/user1/slurm-99999.err "
    "StdOut=/home/user1/slurm-99999.out"
)

# Job with a file path containing whitespace (tests the path-repair logic in get_job_info)
SHOW_JOB_SPACED_PATH = (
    "JobId=99999 JobName=my_job "
    "UserId=user1(12345) GroupId=group1(6789) MCS_label=N/A "
    "Priority=1000 Account=myaccount "
    "JobState=RUNNING "
    "SubmitTime=2024-01-15T08:00:00 EndTime=2024-01-15T09:01:00 "
    "RunTime=00:30:00 "
    "NodeList=node01 "
    "AllocTRES=cpu=4,mem=4G,node=1,billing=4 "
    "Partition=smp "
    "Command=/path/to/a directory/my_script.sh "  # space in path — split on whitespace breaks this
    "WorkDir=/home/user1"
)

# ---------------------------------------------------------------------------
# scontrol show hostname (used to pick a representative node from a partition)
# ---------------------------------------------------------------------------

SHOW_HOSTNAME = "gpu-node01\ngpu-node02\ngpu-node03\ngpu-node04\n"
