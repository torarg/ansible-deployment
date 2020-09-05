class InventoryPlugin:
    """
    Represents the skeleton of an inventory plugin.

    Attributes:
        all_hosts (dict): Dictionary of all hosts.
        deployment_group (dict): Deployment group hosts.
        hosts (dict): Hosts dict representing a hosts.yml file.
        host_vars (dict): Host vars dict.
        group_vars (dict): Group vars dict.
        added_files (list): List of files added to deployment.
    """
    def __init__(self, config):
        self.all_hosts = {}
        self.deployment_group = {}
        self.groups = config.roles
        self.ansible_user = config.ansible_user
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
        self._set_groups()
        self.added_files = []

    def _set_groups(self):
        """
        Set initial inventory groups in self.hosts.
        """
        for group in self.groups:
            group_data = {'children': {}}
            group_data['children']['ansible_deployment'] = None
            self.hosts['all']['children'][group] = group_data

    def update_inventory():
        """
        Update inventory.

        Returns:
            list: List of file names to add to deployment repo.

        Note:
            This function is called from ansible_deployment and
            is required to update the objects inventory attributes and
            return a list of plugin specific files to add to the
            deployment repository.
        """
        return self.added_files
