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
    custom_ca = os.environ.get("VAULT_CA")
    verify = True
    if vault_address is None:
        error = "Environment variable VAULT_ADDR not set"

    if custom_ca is not None:
        verify = custom_ca
    client = hvac.Client(url=vault_address, verify=verify)

    try:
        if not client.is_authenticated():
            error = "Vault authentication error"
    except ConnectionError:
        error = "Vault connection error"

    return (client, error)
