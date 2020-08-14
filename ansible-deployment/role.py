import yaml
from pathlib import Path

class Role:
    """
    Represents an ansible role.

    Args:

    Attributes:
    """

    def __init__(self, role_directory):
        self.path = Path(role_directory)
        self.name = self.path.name
        self.defaults = self._parse_role_sub_directory('defaults')
        self.tasks = self._parse_role_sub_directory('tasks')
        self.files = self._parse_role_sub_directory('files')
        self.handlers = self._parse_role_sub_directory('handlers')
        self.templates = self._parse_role_sub_directory('templates')
        self.meta = self._parse_role_sub_directory('meta')


    def _parse_yaml_file(self, file_path):
        try:
            with open(file_path) as file_stream:
                yaml_data = yaml.safe_load(file_stream)
        except Exception as e:
                yaml_data = e
        return yaml_data


    def _generate_file_info(self, path_object, data):
        return {
            'name': path_object.name,
            'path': path_object,
            'data': data
        }


    def _parse_role_sub_directory(self, sub_directory_name):
        sub_directory_path = self.path / sub_directory_name
        directory_files = {}

        if not sub_directory_path.exists:
            return None


        all_files = list(sub_directory_path.glob('**/*'))
        yaml_files = list(sub_directory_path.glob('**/*.yml'))
        yaml_files += list(sub_directory_path.glob('**/*.yaml'))

        for file_path in all_files:
            file_data = None
            if file_path in yaml_files:
                file_data = self._parse_yaml_file(file_path)
            directory_files[file_path.name] = file_data

        return directory_files
