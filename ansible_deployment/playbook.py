"""
This module contains the Playbook class.
"""

from jinja2 import Environment, PackageLoader, select_autoescape
from ansible_deployment.class_skeleton import AnsibleDeployment


class Playbook(AnsibleDeployment):
    """
    Represents an ansible playbook.

    Args:
        playbook_path (Path): Path object to playbook.
        hosts (str): Playbook target hosts. May be host name or group name.
        roles (sequence): Sequence of role objects.

    Attributes:
        path (Path): Path to playbook.
        name (str): Playbook name.
        hosts (str): Playbook target hosts.
        playbook_data (str): Rendered playbook from template.
    """
    jinja2_env = Environment(loader=PackageLoader('ansible_deployment',
                                                  'templates'),
                             autoescape=select_autoescape(['html', 'xml']),
                             trim_blocks=True)

    def __init__(self, playbook_path, hosts, roles):
        self.path = playbook_path
        self.name = self.path.name
        self.hosts = hosts
        self.roles = roles
        self.playbook_data = self._generate_playbook_data()

    def _generate_playbook_data(self):
        """
        Renders playbook template and returns rendered data.

        Returns:
            str: Rendered playbook data.
        """
        playbook_template = self.jinja2_env.get_template('playbook.yml.j2')
        return playbook_template.render(playbook=self)

    def write(self):
        """
        Write playbook.
        """
        with open(self.path, 'w') as playbook_file_stream:
            playbook_file_stream.write(self.playbook_data)
