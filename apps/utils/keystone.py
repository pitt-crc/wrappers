"""Utility functions for interacting with the Keystone accounting system.

The `keystone` module provides helper functions used across wrapper applications
to authenticate with Keystone, retrieve allocation requests, and summarize
service unit totals per cluster.
"""

from datetime import date
from typing import Any

from keystone_client import KeystoneClient

# Default API configuratipn
KEYSTONE_URL = "https://api.keystone.crcd.pitt.edu"
KEYSTONE_AUTH_ENDPOINT = 'authentication/new/'
RAWUSAGE_RESET_DATE = date.fromisoformat('2024-05-07')


def get_account_id(session: KeystoneClient, account_name: str) -> int:
    """Return the account ID associated with a given account name.

    Args:
        session: An authenticated Keystone client session.
        account_name: The name of the account to query.

    Returns:
        The unique ID value for the given account.
    """

    return session.retrieve_team(filters={'name': account_name})['results'][0]['id']


def get_active_requests(session: KeystoneClient, account_name: str) -> list[dict]:
    """Return all active allocation requests for a given Slurm account.

    Args:
        session: An authenticated Keystone client session.
        account_name: The name of the Slurm account to query.

    Returns:
        A list of active allocation request records.
    """

    today = date.today().isoformat()
    team_id = get_account_id(session, account_name)

    return session.retrieve_request(
        filters={
            'team': team_id,
            'status': 'AP',
            'active__lte': today,
            'expire__gt': today,
        }
    )['results']


def get_request_allocations(session: KeystoneClient, request_pk: int) -> list[dict]:
    """Return all allocations associated with a given allocation request.

    Args:
        session: An authenticated Keystone client session.
        request_pk: The primary key of the allocation request.

    Returns:
        A list of allocation records for the given request.
    """

    return session.retrieve_allocation(filters={'request': request_pk})['results']


def get_earliest_startdate(alloc_requests: list[dict]) -> date:
    """Return the earliest start date across a set of allocation requests.

    The result is clamped to the most recent raw usage reset date to ensure
    reported usage does not exceed 100% of the awarded allocation.

    Args:
        alloc_requests: A list of allocation request records.

    Returns:
        The earliest valid start date for usage reporting.
    """

    earliest_date = date.today()
    for request in alloc_requests:
        start = date.fromisoformat(request['active'])
        if start < earliest_date:
            earliest_date = start

    return max(earliest_date, RAWUSAGE_RESET_DATE)


def get_most_recent_expired_request(session: KeystoneClient, account_name: str) -> dict:
    """Return the single most recently expired allocation request for a given account.

    Args:
        session: An authenticated Keystone client session.
        account_name: The name of the Slurm account to query.

    Returns:
        The most recently expired allocation request record.
    """

    today = date.today().isoformat()
    team_id = get_account_id(session, account_name)

    return session.retrieve_request(
        order='-expire',
        filters={
            'team': team_id,
            'status': 'AP',
            'expire__lte': today,
        }
    )['results'][0]


def get_enabled_cluster_ids(session: KeystoneClient) -> dict[int, str]:
    """Return a mapping of cluster IDs to cluster names for all enabled clusters.

    Args:
        session: An authenticated Keystone client session.

    Returns:
        A dictionary mapping cluster ID to cluster name.
    """

    return {
        cluster['id']: cluster['name']
        for cluster in session.retrieve_cluster(filters={'enabled': True})['results']
    }


def get_per_cluster_totals(
    session: KeystoneClient,
    alloc_requests: list[dict],
    clusters: dict[int, str],
    per_request: bool = False,
) -> dict[str, Any]:
    """Return the total awarded service units per cluster across a set of allocation requests.

    When `per_request` is True, totals are nested under each request ID. Otherwise,
    totals are aggregated across all requests.

    Args:
        session: An authenticated Keystone client session.
        alloc_requests: A list of allocation request records.
        clusters: A mapping of cluster ID to cluster name.
        per_request: Whether to return totals broken out by request ID.

    Returns:
        A dictionary of awarded service unit totals keyed by cluster name, or by
        request ID and then cluster name when `per_request` is True.
    """

    per_cluster_totals: dict[str, Any] = {}
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
