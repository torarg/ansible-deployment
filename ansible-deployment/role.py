import yaml
from pathlib import Path

class Role:
    """
    Represents an ansible role.

    Args:
        role_directory (str): Path to role directory.

    Attributes:
        path (Path): Path object.
        name (str): Role name extracted from path.
        defaults (dict): sub directory file information with parsed yaml data.
        vars (dict): sub directory file information with parsed yaml data.
        tasks (dict): sub directory file information with parsed yaml data.
        files (dict): sub directory file information with parsed yaml data.
        handlers (dict): sub directory file information with parsed yaml data.
        templates (dict): sub directory file information with parsed yaml data.
        meta (dict): sub directory file information with parsed yaml data.

    Notes:
        The attributes containing role sub directory information are 'None'
        if the corresponding sub directory does not exist.
    """

    def __init__(self, role_directory):
        self.path = Path(role_directory)
        self.name = self.path.name
        self.defaults = self._parse_role_sub_directory('defaults')
        self.vars = self._parse_role_sub_directory('vars')
        self.tasks = self._parse_role_sub_directory('tasks')
        self.files = self._parse_role_sub_directory('files')
        self.handlers = self._parse_role_sub_directory('handlers')
        self.templates = self._parse_role_sub_directory('templates')
        self.meta = self._parse_role_sub_directory('meta')


    def _parse_yaml_file(self, file_path):
        """
        Parses a given yaml_file.

        Arguments:
            file_path (Path): Path object to yaml file.

        Returns:
            Parsed yaml data.
        """
        try:
            with open(file_path) as file_stream:
                yaml_data = yaml.safe_load(file_stream)
        except Exception as e:
                yaml_data = e
        return yaml_data


    def _generate_file_info(self, path_object, data):
        """
        Generates a dictionary containing file information.

        Args:
            path_object (Path): Path object representing file path.
            data: Parsed data from file.

        Returns:
            dict: File information dictionary.
        """
        return {
            'name': path_object.name,
            'path': path_object,
            'data': data
        }


    def _parse_role_sub_directory(self, sub_directory_name):
        """
        Parses an ansible role sub directory.

        Args:
            sub_directory_name (str): Name of sub directory.

        Returns:
            dict: A file based dictionary. None if directory does not exist.
        """
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
