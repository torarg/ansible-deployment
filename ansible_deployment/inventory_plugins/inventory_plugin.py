class InventoryPlugin:
    """
    Represents the skeleton of an inventory plugin.

    Attributes:
        all_hosts (dict): Dictionary of all hosts.
        deployment_group (dict): Deployment group hosts.
        hosts (dict): Hosts dict representing a hosts.yml file.
        host_vars (dict): Host vars dict.
        group_vars (dict): Group vars dict.
    """
    def __init__(self):
        self.all_hosts = {}
        self.deployment_group = {}
        self.hosts = {
            'all': {
                'hosts': self.all_hosts,
                'children': {
                    'ansible_deployment': {
                        'hosts': self.deployment_group
                    }
                }
            }
        }
        self.host_vars = {}
        self.group_vars = {}

    def update_inventory():
        """
        Update inventory.

        This function is called from ansible_deployment and
        is required to update the objects inventory attributes.
        """
        pass
