"""Utility functions used across various wrappers for interacting with keystone"""

from datetime import date
from typing import Any, Dict, Literal, Optional, Union

import requests

# Custom types
ResponseContentType = Literal['json', 'text', 'content']
ParsedResponseContent = Union[Dict[str, Any], str, bytes]

# Default API configuratipn
KEYSTONE_URL = "https://keystone.crc.pitt.edu"
KEYSTONE_AUTH_ENDPOINT = 'authentication/new'
RAWUSAGE_RESET_DATE = date.fromisoformat('2024-05-07')


class KeystoneApi:
    """API client for submitting requests to the Keystone API"""

    def __init__(self, base_url: str = KEYSTONE_URL) -> None:
        """Initializes the KeystoneApi class with the base URL of the API.

        Args:
            base_url: The base URL of the Keystone API
        """

        self.base_url = base_url
        self._token: Optional[str] = None

    def login(self, username: str, password: str, endpoint: str = KEYSTONE_AUTH_ENDPOINT) -> None:
        """Logs in to the Keystone API and caches the JWT token.

        Args:
            username: The username for authentication
            password: The password for authentication
            endpoint: The API endpoint to send the authentication request to

        Raises:
            requests.HTTPError: If the login request fails
        """

        response = requests.post(f"{self.base_url}/{endpoint}", json={"username": username, "password": password})
        response.raise_for_status()
        self._token = response.json().get("token")

    def _get_headers(self) -> Dict[str, str]:
        """Constructs the headers for an authenticated request.

        Returns:
            A dictionary of headers including the Authorization token

        Raises:
            ValueError: If the authentication token is not found
        """

        if not self._token:
            raise ValueError("Authentication token not found. Please login first.")

        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _process_response(response: requests.Response, response_type: ResponseContentType) -> ParsedResponseContent:
        """Processes the response based on the expected response type.

        Args:
            response: The response object
            response_type: The expected response type ('json', 'text', 'content')

        Returns:
            The response in the specified format

        Raises:
            ValueError: If the response type is invalid
        """

        if response_type == 'json':
            return response.json()

        elif response_type == 'text':
            return response.text

        elif response_type == 'content':
            return response.content

        else:
            raise ValueError(f"Invalid response type: {response_type}")

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, response_type: ResponseContentType = 'json'
    ) -> ParsedResponseContent:
        """Makes a GET request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the GET request to
            params: The query parameters to include in the request
            response_type: The expected response type ('json', 'text', 'content')

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the GET request fails
        """

        response = requests.get(f"{self.base_url}/{endpoint}", headers=self._get_headers(), params=params)
        response.raise_for_status()
        return self._process_response(response, response_type)

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, response_type: ResponseContentType = 'json'
    ) -> ParsedResponseContent:
        """Makes a POST request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the POST request to
            data: The JSON data to include in the POST request
            response_type: The expected response type ('json', 'text', 'content')

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the POST request fails
        """

        response = requests.post(f"{self.base_url}/{endpoint}", headers=self._get_headers(), json=data)
        response.raise_for_status()
        return self._process_response(response, response_type)

    def patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, response_type: ResponseContentType = 'json'
    ) -> ParsedResponseContent:
        """Makes a PATCH request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the PATCH request to
            data: The JSON data to include in the PATCH request
            response_type: The expected response type ('json', 'text', 'content')

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the PATCH request fails
        """

        response = requests.patch(f"{self.base_url}/{endpoint}", headers=self._get_headers(), json=data)
        response.raise_for_status()
        return self._process_response(response, response_type)

    def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, response_type: ResponseContentType = 'json'
    ) -> ParsedResponseContent:
        """Makes a PUT request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the PUT request to
            data: The JSON data to include in the PUT request
            response_type: The expected response type ('json', 'text', 'content')

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the PUT request fails
        """

        response = requests.put(f"{self.base_url}/{endpoint}", headers=self._get_headers(), json=data)
        response.raise_for_status()
        return self._process_response(response, response_type)

    def delete(self, endpoint: str, response_type: ResponseContentType = 'json') -> ParsedResponseContent:
        """Makes a DELETE request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the DELETE request to
            response_type: The expected response type ('json', 'text', 'content')

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the DELETE request fails
        """

        response = requests.delete(f"{self.base_url}/{endpoint}", headers=self._get_headers())
        response.raise_for_status()
        return self._process_response(response, response_type)


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

    today = date.today().isoformat()
    response = requests.get(
        f"{keystone_url}/allocations/requests/?group={group_pk}&status=AP&active__lte={today}&expire__gt={today}",
        headers=auth_header)
    response.raise_for_status()
    return [request for request in response.json()]


def get_researchgroup_id(keystone_url: str, account_name: str, auth_header: dict) -> int:
    """Get the Researchgroup ID from keystone for the specified Slurm account"""

    response = requests.get(f"{keystone_url}/users/researchgroups/?name={account_name}", headers=auth_header)
    response.raise_for_status()

    try:
        group_id = int(response.json()[0]['id'])
    except IndexError:
        print(f"No Slurm Account found in the accounting system for '{account_name}'. \n"
              f"Please submit a ticket to the CRC team to ensure your allocation was properly configured")
        exit()

    return group_id


def get_earliest_startdate(alloc_requests: [dict]) -> date:
    """Given a number of requests, determine the earliest start date across them. This takes the most recent rawusage
    reset into account for accuracy against current limits and to prevent seeing >100% usage."""

    earliest_date = date.today()
    for request in alloc_requests:
        start = date.fromisoformat(request['active'])
        if start < earliest_date:
            earliest_date = start

    return max(earliest_date, RAWUSAGE_RESET_DATE)


def get_most_recent_expired_request(keystone_url: str, group_pk: int, auth_header: dict) -> [dict]:
    """Get the single most recently expired AllocationRequest information from keystone for a given group"""

    today = date.today().isoformat()
    response = requests.get(
        f"{keystone_url}/allocations/requests/?ordering=-expire&group={group_pk}&status=AP&expire__lte={today}",
        headers=auth_header)
    response.raise_for_status()

    return [response.json()[0]]


def get_enabled_cluster_ids(keystone_url: str, auth_header: dict) -> dict():
    """Get the list of enabled clusters defined in Keystone along with their IDs"""

    response = requests.get(f"{keystone_url}/allocations/clusters/?enabled=True", headers=auth_header)
    response.raise_for_status()
    clusters = {}
    for cluster in response.json():
        clusters[cluster['id']] = cluster['name']

    return clusters


def get_per_cluster_totals(alloc_requests: [dict],
                           clusters: dict,
                           auth_header: dict,
                           per_request: bool = False) -> dict:
    """Gather the awarded totals across the given requests on each cluster into a dictionary"""

    per_cluster_totals = {}
    for request in alloc_requests:
        if per_request:
            per_cluster_totals[request['id']] = {}
        for allocation in get_request_allocations(KEYSTONE_URL, request['id'], auth_header):
            cluster = clusters[allocation['cluster']]
            if per_request:
                per_cluster_totals[request['id']].setdefault(cluster, 0)
                per_cluster_totals[request['id']][cluster] += allocation['awarded']
            else:
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += allocation['awarded']

    return per_cluster_totals
