"""Utility functions used across various wrappers for interacting with keystone"""

from datetime import date
from typing import Any, Dict, Literal, Union

from keystone_client import KeystoneClient

# Custom types
ResponseContentType = Literal['json', 'text', 'content']
ParsedResponseContent = Union[Dict[str, Any], str, bytes]

# Default API configuratipn
KEYSTONE_URL = "https://keystone.crc.pitt.edu"
KEYSTONE_AUTH_ENDPOINT = 'authentication/new/'
RAWUSAGE_RESET_DATE = date.fromisoformat('2024-05-07')


def get_request_allocations(session: KeystoneClient, request_pk: int) -> dict:
    """Get All Allocation information from keystone for a given request"""

    return session.retrieve_allocation(filters={'request': request_pk})


def get_active_requests(session: KeystoneClient, account_name: str) -> list[dict]:
    """Get all active AllocationRequest information from keystone for a given team"""

    today = date.today().isoformat()
    return session.retrieve_request(
        filters={'team__name': account_name, 'status': 'AP', 'active__lte': today, 'expire__gt': today})


def get_earliest_startdate(alloc_requests: [dict]) -> date:
    """Given a number of requests, determine the earliest start date across them. This takes the most recent rawusage
    reset into account for accuracy against current limits and to prevent seeing >100% usage."""

    earliest_date = date.today()
    for request in alloc_requests:
        start = date.fromisoformat(request['active'])
        if start < earliest_date:
            earliest_date = start

    return max(earliest_date, RAWUSAGE_RESET_DATE)


def get_most_recent_expired_request(session: KeystoneClient, account_name: str) -> list[dict]:
    """Get the single most recently expired AllocationRequest information from keystone for a given team"""

    today = date.today().isoformat()
    return session.retrieve_request(
        order='-expire',
        filters={'team__name': account_name, 'status': 'AP', 'expire__lte': today})[0]


def get_enabled_cluster_ids(session: KeystoneClient) -> dict:
    """Get the list of enabled clusters defined in Keystone along with their IDs"""

    clusters = {}
    for cluster in session.retrieve_cluster(filters={'enabled': True}):
        clusters[cluster['id']] = cluster['name']

    return clusters


def get_per_cluster_totals(session: KeystoneClient, alloc_requests: [dict], clusters: dict,
                           per_request: bool = False) -> dict:
    """Gather the awarded totals across the given requests on each cluster into a dictionary"""

    per_cluster_totals = {}
    for request in alloc_requests:
        if per_request:
            per_cluster_totals[request['id']] = {}
        for allocation in get_request_allocations(session, request['id']):
            cluster = clusters[allocation['cluster']]
            awarded = allocation['awarded'] if allocation['awarded'] is not None else 0
            if per_request:
                per_cluster_totals[request['id']].setdefault(cluster, 0)
                per_cluster_totals[request['id']][cluster] += awarded
            else:
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += awarded

    return per_cluster_totals
