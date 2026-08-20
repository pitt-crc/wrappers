"""Utility functions for interacting with the Keystone accounting system.

The `keystone` module provides helper functions used across wrapper applications
to authenticate with Keystone, retrieve allocation requests, and summarize
service unit totals per cluster.
"""

from datetime import date
from typing import Any

from keystone_client import KeystoneClient

# Default API configuration
KEYSTONE_URL = "https://api.keystone.crcd.pitt.edu"
KEYSTONE_AUTH_ENDPOINT = 'authentication/new/'
RAWUSAGE_RESET_DATE = date.fromisoformat('2024-05-07')


def authenticate_keystone_session(username: str, password: str) -> KeystoneClient:
    """Create and return an authenticated Keystone client session.

    Args:
        username: The username to authenticate with.
        password: The password to authenticate with.

    Returns:
        An authenticated Keystone client session.
    """

    session = KeystoneClient(base_url=KEYSTONE_URL)

    try:
        session.login(username=username, password=password)

    except Exception:
        raise ValueError(
            'ERROR: authentication failed. '
            'Please check your username and password and try again.'
        )

    return session


def _get_results(session: KeystoneClient, endpoint: str, params: dict) -> list[dict]:
    """Issue a GET request against the given endpoint and return the parsed results list.

    Args:
        session: An authenticated Keystone client session.
        endpoint: The API endpoint to query.
        params: Query parameters to include in the request.

    Returns:
        The `results` list from the endpoint's JSON response.
    """

    request = session.http_get(endpoint, params=params)
    request.raise_for_status()
    return request.json()['results']


def get_team_id(session: KeystoneClient, account_name: str) -> int:
    """Return the account ID associated with a given account name.

    Args:
        session: An authenticated Keystone client session.
        account_name: The name of the account to query.

    Returns:
        The unique ID value for the given account.
    """

    results = _get_results(session, '/users/teams/', params={'name': account_name})
    return results[0]['id']


def get_active_requests(session: KeystoneClient, account_name: str) -> list[dict]:
    """Return all active allocation requests for a given Slurm account.

    Args:
        session: An authenticated Keystone client session.
        account_name: The name of the Slurm account to query.

    Returns:
        A list of active allocation request records.
    """

    today = date.today().isoformat()
    team_id = get_team_id(session, account_name)

    return _get_results(
        session,
        '/allocations/requests/',
        params={
            'team': team_id,
            'status': 'AP',
            'active__lte': today,
            'expire__gt': today,
        })


def get_most_recent_expired_request(session: KeystoneClient, account_name: str) -> dict:
    """Return the single most recently expired allocation request for a given account.

    Args:
        session: An authenticated Keystone client session.
        account_name: The name of the Slurm account to query.

    Returns:
        The most recently expired allocation request record.
    """

    today = date.today().isoformat()
    team_id = get_team_id(session, account_name)

    results = _get_results(
        session,
        '/allocations/requests/',
        params={
            'team': team_id,
            'status': 'AP',
            'expire__lte': today,
            'order': '-expire',
        })

    return results[0]


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


def get_per_cluster_totals(alloc_requests: list[dict], per_request: bool = False) -> dict[str, Any]:
    """Return the total awarded service units per cluster across a set of allocation requests.

    When `per_request` is True, totals are nested under each request ID. Otherwise,
    totals are aggregated across all requests.

    Args:
        alloc_requests: A list of allocation request records.
        per_request: Whether to return totals broken out by request ID.

    Returns:
        A dictionary of awarded service unit totals keyed by cluster name, or by
        request ID and then cluster name when `per_request` is True.
    """

    per_cluster_totals: dict[str, Any] = {}

    for request in alloc_requests:
        if per_request:
            per_cluster_totals[request['id']] = {}

        for allocation in request['_allocations']:
            cluster = allocation['_cluster']['name']
            awarded = allocation['awarded'] if allocation['awarded'] is not None else 0

            if per_request:
                per_cluster_totals[request['id']].setdefault(cluster, 0)
                per_cluster_totals[request['id']][cluster] += awarded

            else:
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += awarded

    return per_cluster_totals
