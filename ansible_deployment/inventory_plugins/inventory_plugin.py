class InventoryPlugin:
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
        pass
