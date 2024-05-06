"""Utility functions used across various wrappers for interacting with keystone"""

import requests
from datetime import date

KEYSTONE_URL = "https://keystone.crc.pitt.edu"
CLUSTERS = {1: 'MPI', 2: 'SMP', 3: 'HTC', 4: 'GPU'}


def get_auth_header(keystone_url: str, auth_header: dict) -> dict:
    """ Generate an authorization header to be used for accessing information from keystone"""

    response = requests.post(f"{keystone_url}/authentication/new/", json=auth_header)
    response.raise_for_status()
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access']}"}


def get_allocations_all(keystone_url: str, auth_header: dict) -> dict:
    """Get All Resource Allocation information from keystone for the user"""

    response = requests.get(f"{keystone_url}/allocations/allocations/", headers=auth_header)
    response.raise_for_status()
    return response.json()


def get_allocation_requests(keystone_url: str, group_pk: int, auth_header: dict) -> dict:
    """Get all Resource Allocation Request information from keystone"""

    today = date.today().isoformat()

    response = requests.get(f"{keystone_url}/allocations/requests/?group={group_pk}&status=AP",headers=auth_header)
    response.raise_for_status()
    return response.json()


def get_researchgroups(keystone_url: str, auth_header: dict) -> dict:
    """Get all Resource Allocation Request information from keystone"""

    response = requests.get(f"{keystone_url}/users/researchgroups/", headers=auth_header)
    response.raise_for_status()
    return response.json()


def get_cluster_usage(account_name: str, start_date: date, cluster: str) -> int:
    """Return the total billable usage in hours for a given Slurm account

    Args:
        account_name: The name of the account to get usage for
        cluster: The name of the cluster to get usage on

    Returns:
        An integer representing the total (historical + current) billing TRES hours usage from sshare
    """

    start = start_date.isoformat()
    cmd = split(f"sreport -nP cluster accountutilizationbyuser Cluster={cluster} Account={account_name} -t Hours Start={start} -T Billing Format=Proper,Used")

    try:
        total, *data = subprocess_call(cmd).split('\n')
    except ValueError:
        return None

    out_data = dict()
    out_date['total'] = total
    for line in data:
        user, usage = line.split('|')
        usage = int(usage)
        out_data[user] = usage

    return out_data


def subprocess_call(args: list[str]) -> str:
    """Wrapper method for executing shell commands via ``Popen.communicate``

    Args:
        args: A sequence of program arguments

    Returns:
        The piped output to STDOUT
    """

    process = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()

    if process.returncode != 0:
        message = f"Error executing shell command: {' '.join(args)} \n {err.decode('utf-8').strip()}"
        raise RuntimeError(message)

    return out.decode("utf-8").strip()
