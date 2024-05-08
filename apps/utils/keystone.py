"""Utility functions used across various wrappers for interacting with keystone"""

from datetime import date

import requests

KEYSTONE_URL = "https://keystone.crc.pitt.edu"
CLUSTERS = {1: 'MPI', 2: 'SMP', 3: 'HTC', 4: 'GPU'}


def get_auth_header(keystone_url: str, auth_header: dict) -> dict:
    """ Generate an authorization header to be used for accessing information from keystone"""

    response = requests.post(f"{keystone_url}/authentication/new/", json=auth_header)
    response.raise_for_status()
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access']}"}


def get_request_allocations(keystone_url: str, request_pk: int, auth_header: dict) -> dict:
    """Get All Allocation information from keystone for a given request"""

    response = requests.get(f"{keystone_url}/allocations/allocations/?request={request_pk}", headers=auth_header)
    response.raise_for_status()
    return response.json()


def get_active_requests(keystone_url: str, group_pk: int, auth_header: dict) -> [dict]:
    """Get all active AllocationRequest information from keystone for a given group"""

    response = requests.get(f"{keystone_url}/allocations/requests/?group={group_pk}&status=AP", headers=auth_header)
    response.raise_for_status()
    return [request for request in response.json()
            if date.fromisoformat(request['active']) <= date.today() < date.fromisoformat(request['expire'])]


def get_researchgroup_id(keystone_url: str, account_name: str, auth_header: dict) -> int:
    """Get the Researchgroup ID from keystone for the specified Slurm account"""

    response = requests.get(f"{keystone_url}/users/researchgroups/?name={account_name}", headers=auth_header)
    response.raise_for_status()

    try:
        group_id = int(response.json()[0]['id'])
    except:
        group_id = None

    return group_id


def get_earliest_startdate(alloc_requests: [dict]) -> date:
    """Given a number of requests, determine the earliest start date across them"""

    earliest_date = date.today()
    for request in alloc_requests:
        start = date.fromisoformat(request['active'])
        if start < earliest_date:
            earliest_date = start

    return earliest_date


def get_per_cluster_totals(alloc_requests: [dict], auth_header: dict, per_request: bool = False) -> dict:
    """Gather the awarded totals across the given requests on each cluster into a dictionary"""

    per_cluster_totals = {}
    for request in alloc_requests:
        if per_request:
            per_cluster_totals[request['id']] = {}
        for allocation in get_request_allocations(KEYSTONE_URL, request['id'], auth_header):
            cluster = CLUSTERS[allocation['cluster']]
            if per_request:
                per_cluster_totals[request['id']].setdefault(cluster, 0)
                per_cluster_totals[request['id']][cluster] += allocation['awarded']
            else:
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += allocation['awarded']

    return per_cluster_totals
