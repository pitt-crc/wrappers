"""Utility functions used across various wrappers for interacting with keystone"""

import requests

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


def get_allocation_requests(keystone_url: str, auth_header: dict) -> dict:
    """Get all Resource Allocation Request information from keystone"""

    response = requests.get(f"{keystone_url}/allocations/requests/", headers=auth_header)
    response.raise_for_status()
    return response.json()