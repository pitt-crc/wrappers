"""Utility functions used across various wrappers for interacting with keystone"""

from datetime import date
from typing import Any, Dict, List, Literal, Optional, Union

import requests
from requests import HTTPError

# Custom types
ResponseContentType = Literal['json', 'text', 'content']
ParsedResponseContent = Union[Dict[str, Any], str, bytes]
RecordQueryResult = Union[None, dict, List[dict]]

# CRC specific API settings
KEYSTONE_URL = "https://keystone.crc.pitt.edu"
RAWUSAGE_RESET_DATE = date.fromisoformat('2024-05-07')


class KeystoneApi:
    """API client for submitting requests to the Keystone API"""

    timeout = 10
    authentication_endpoint = 'authentication/new/'
    allocations_endpoint = 'allocations/allocations/'
    requests_endpoint = 'allocations/requests/'
    research_group_endpoint = 'users/researchgroups/'
    users_endpoint = 'users/users/'

    def __init__(self, base_url: str = KEYSTONE_URL) -> None:
        """Initializes the KeystoneApi class with the base URL of the API.

        Args:
            base_url: The base URL of the Keystone API
        """

        self.base_url = base_url
        self._token: Optional[str] = None

    def login(
        self,
        username: str,
        password: str,
        timeout: int = timeout
    ) -> None:
        """Logs in to the Keystone API and caches the JWT token.

        Args:
            username: The username for authentication
            password: The password for authentication
            timeout: Number of seconds before he requests times out

        Raises:
            requests.HTTPError: If the login request fails
        """

        response = requests.post(
            f"{self.base_url}/{self.authentication_endpoint}",
            json={"username": username, "password": password},
            timeout=timeout
        )

        response.raise_for_status()
        self._token = response.json().get("access")

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
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        response_type: ResponseContentType = 'json',
        timeout: int = timeout
    ) -> ParsedResponseContent:
        """Makes a GET request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the GET request to
            params: The query parameters to include in the request
            response_type: The expected response type ('json', 'text', 'content')
            timeout: Number of seconds before he requests times out

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the GET request fails
        """

        response = requests.get(
            f"{self.base_url}/{endpoint}",
            headers=self._get_headers(),
            params=params,
            timeout=timeout
        )

        response.raise_for_status()
        return self._process_response(response, response_type)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        response_type: ResponseContentType = 'json',
        timeout: int = timeout
    ) -> ParsedResponseContent:
        """Makes a POST request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the POST request to
            data: The JSON data to include in the POST request
            response_type: The expected response type ('json', 'text', 'content')
            timeout: Number of seconds before he requests times out

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the POST request fails
        """

        response = requests.post(
            f"{self.base_url}/{endpoint}",
            headers=self._get_headers(),
            json=data,
            timeout=timeout
        )

        response.raise_for_status()
        return self._process_response(response, response_type)

    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        response_type: ResponseContentType = 'json',
        timeout: int = timeout
    ) -> ParsedResponseContent:
        """Makes a PATCH request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the PATCH request to
            data: The JSON data to include in the PATCH request
            response_type: The expected response type ('json', 'text', 'content')
            timeout: Number of seconds before he requests times out

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the PATCH request fails
        """

        response = requests.patch(
            f"{self.base_url}/{endpoint}",
            headers=self._get_headers(),
            json=data,
            timeout=timeout
        )

        response.raise_for_status()
        return self._process_response(response, response_type)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        response_type: ResponseContentType = 'json',
        timeout: int = timeout
    ) -> ParsedResponseContent:
        """Makes a PUT request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the PUT request to
            data: The JSON data to include in the PUT request
            response_type: The expected response type ('json', 'text', 'content')
            timeout: Number of seconds before he requests times out

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the PUT request fails
        """

        response = requests.put(
            f"{self.base_url}/{endpoint}",
            headers=self._get_headers(),
            json=data,
            timeout=timeout
        )

        response.raise_for_status()
        return self._process_response(response, response_type)

    def delete(
        self,
        endpoint: str,
        response_type: ResponseContentType = 'json',
        timeout: int = timeout
    ) -> ParsedResponseContent:
        """Makes a DELETE request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the DELETE request to
            response_type: The expected response type ('json', 'text', 'content')
            timeout: Number of seconds before he requests times out

        Returns:
            The response from the API in the specified format

        Raises:
            requests.HTTPError: If the DELETE request fails
        """

        response = requests.delete(f"{self.base_url}/{endpoint}", headers=self._get_headers(), timeout=timeout)
        response.raise_for_status()
        return self._process_response(response, response_type)

    def _get_records(
        self,
        endpoint: str,
        pk: Optional[int] = None,
        filters: Optional[dict] = None,
        timeout=timeout
    ) -> RecordQueryResult:
        """Fetch data from the specified endpoint with optional primary key and filters

        Args:
            endpoint: The API endpoint to send the GET request to
            pk: Optional primary key to fetch a specific record
            filters: Optional query parameters to include in the request

        Returns:
            The response from the API in JSON format
        """

        if pk is not None:
            endpoint = f'{endpoint}{pk}/'

        try:
            return self.get(endpoint, params=filters, timeout=timeout)

        except HTTPError as excep:
            if excep.response.status_code == 404:
                return None

            raise

    def get_allocation(
        self,
        pk: Optional[int] = None,
        timeout: int = timeout,
        **filters
    ) -> RecordQueryResult:
        """Return allocation data from the API

        Args:
            pk: Optional primary key to fetch a specific allocation
            timeout: Number of seconds before he requests times out
            **filters: Additional filters to apply to the request

        Returns:
            A list of allocation records
        """

        return self._get_records(self.allocations_endpoint, pk, filters, timeout)

    def get_allocation_request(
        self,
        pk: Optional[int] = None,
        timeout: int = timeout,
        **filters
    ) -> RecordQueryResult:
        """Return allocation request data from the API

        Args:
            pk: Optional primary key to fetch a specific allocation request
            timeout: Number of seconds before he requests times out
            **filters: Additional filters to apply to the request

        Returns:
            A list of allocation request records
        """

        return self._get_records(self.requests_endpoint, pk, filters, timeout)

    def get_research_group(
        self,
        pk: Optional[int] = None,
        timeout: int = timeout,
        **filters
    ) -> RecordQueryResult:
        """Return research group data from the API

        Args:
            pk: Optional primary key to fetch a specific research group
            timeout: Number of seconds before he requests times out
            **filters: Additional filters to apply to the request

        Returns:
            A list of research group records
        """

        return self._get_records(self.research_group_endpoint, pk, filters, timeout)

    def get_user(self, pk: Optional[int] = None, timeout: int = timeout, **filters) -> RecordQueryResult:
        """Return user data from the API

        Args:
            pk: Optional primary key to fetch a specific user
            timeout: Number of seconds before he requests times out
            **filters: Additional filters to apply to the request

        Returns:
            A list of user records
        """

        return self._get_records(self.users_endpoint, pk, filters, timeout)


def get_request_allocations(keystone_client: KeystoneApi, request_pk: int) -> dict:
    """Get All Allocation information from keystone for a given request"""

    return keystone_client.get('allocations/allocations/', {'request': request_pk}, 'json')


def get_active_requests(keystone_client: KeystoneApi, group_pk: int) -> [dict]:
    """Get all active AllocationRequest information from keystone for a given group"""

    today = date.today().isoformat()
    return [request for request in keystone_client.get('allocations/requests/',
                                                       {'group': group_pk,
                                                        'status': 'AP',
                                                        'active__lte': today,
                                                        'expire__gt': today},
                                                       'json'
                                                       )]


def get_researchgroup_id(keystone_client: KeystoneApi, account_name: str) -> int:
    """Get the Researchgroup ID from keystone for the specified Slurm account"""

    # Attempt to get the primary key for the ResearchGroup
    try:
        keystone_group_id = keystone_client.get('users/researchgroups/',
                                                {'name': account_name},
                                                'json')[0]['id']
    except IndexError:
        print(f"No Slurm Account found in the accounting system for '{account_name}'. \n"
              f"Please submit a ticket to the CRC team to ensure your allocation was properly configured")
        exit()

    return keystone_group_id


def get_earliest_startdate(alloc_requests: [dict]) -> date:
    """Given a number of requests, determine the earliest start date across them. This takes the most recent rawusage
    reset into account for accuracy against current limits and to prevent seeing >100% usage."""

    earliest_date = date.today()
    for request in alloc_requests:
        start = date.fromisoformat(request['active'])
        if start < earliest_date:
            earliest_date = start

    return max(earliest_date, RAWUSAGE_RESET_DATE)


def get_most_recent_expired_request(keystone_client: KeystoneApi, group_pk: int) -> [dict]:
    """Get the single most recently expired AllocationRequest information from keystone for a given group"""

    today = date.today().isoformat()
    return [keystone_client.get('allocations/requests/',
                                {'group': group_pk,
                                 'status': 'AP',
                                 'ordering': '-expire',
                                 'expire__lte': today},
                                'json'
                                )[0]]


def get_enabled_cluster_ids(keystone_client: KeystoneApi) -> dict():
    """Get the list of enabled clusters defined in Keystone along with their IDs"""

    clusters = {}
    for cluster in keystone_client.get('allocations/clusters/', {'enabled': True}, 'json'):
        clusters[cluster['id']] = cluster['name']

    return clusters


def get_per_cluster_totals(keystone_client: KeystoneApi,
                           alloc_requests: [dict],
                           clusters: dict,
                           per_request: bool = False) -> dict:
    """Gather the awarded totals across the given requests on each cluster into a dictionary"""

    per_cluster_totals = {}
    for request in alloc_requests:
        if per_request:
            per_cluster_totals[request['id']] = {}
        for allocation in get_request_allocations(keystone_client, request['id']):
            cluster = clusters[allocation['cluster']]
            if per_request:
                per_cluster_totals[request['id']].setdefault(cluster, 0)
                per_cluster_totals[request['id']][cluster] += allocation['awarded']
            else:
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += allocation['awarded']

    return per_cluster_totals
