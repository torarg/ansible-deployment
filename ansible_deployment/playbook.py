from jinja2 import Environment, PackageLoader, select_autoescape


class Playbook:
    jinja2_env = Environment(
        loader=PackageLoader('ansible_deployment', 'templates'),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True
    )
    def __init__(self, playbook_path, hosts, roles):
        self.path = playbook_path
        self.name = self.path.name
        self.hosts = hosts
        self.roles = roles
        self.playbook_data = self._generate_playbook_data()

    def _generate_playbook_data(self):
        playbook_template = self.jinja2_env.get_template('playbook.yml.j2')
        return playbook_template.render(playbook=self)

    def write(self):
        with open(self.path, 'w') as playbook_file_stream:
            playbook_file_stream.write(self.playbook_data)
