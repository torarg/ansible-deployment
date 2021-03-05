"""
Vault inventory plugin.
"""
import hvac
import os
from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin


class Vault(InventoryPlugin):
    """
    Vault InventoryPlugin class.
    """

    def init_vault_client(self):
        """
        Initializes vault client.

        Returns:
            (hvac.v1.Client, String): Vault client instance and error message
        """
        client = None
        error = None
        vault_address = os.environ.get("VAULT_ADDR")
        if vault_address is None:
            error = "VAULT_ADDR not set"

        client = hvac.Client(url=vault_address)

        try:
            if not client.is_authenticated():
                error = "Authentication error"
        except ConnectionError:
            error = "Connection error"

        return (client, error)
