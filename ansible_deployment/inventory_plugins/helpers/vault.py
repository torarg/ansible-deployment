"""
Vault helpers.
"""
import hvac
import os


def init_vault_client():
    """
    Initializes vault client.

    Returns:
        (hvac.v1.Client, String): Vault client instance and error message
    """
    client = None
    error = None
    vault_address = os.environ.get("VAULT_ADDR")
    if vault_address is None:
        error = "vault: VAULT_ADDR not set"

    client = hvac.Client(url=vault_address)

    try:
        if not client.is_authenticated():
            error = "vault: Authentication error"
    except ConnectionError:
        error = "vault: Connection error"

    return (client, error)
