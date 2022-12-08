"""
This module contains the Role class.
"""

import shutil
from pathlib import Path
import yaml
from ansible_deployment import AnsibleDeployment


class Role(AnsibleDeployment):
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
    filtered_attributes = [
        'vars', 'defaults', 'tasks', 'handlers', 'meta', 'files', 'templates'
    ]

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

    @staticmethod
    def _parse_yaml_file(file_path):
        """
        Parses a given yaml_file.

        Arguments:
            file_path (Path): Path object to yaml file.

        Returns:
            Parsed yaml data.
        """
        with open(file_path) as file_stream:
            yaml_data = yaml.safe_load(file_stream)
        return yaml_data

    @staticmethod
    def _generate_file_info(path_object, data):
        """
        Generates a dictionary containing file information.

        Args:
            path_object (Path): Path object representing file path.
            data: Parsed data from file.

        Returns:
            dict: File information dictionary.
        """
        return {'name': path_object.name, 'path': path_object, 'data': data}

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
            file_info = self._generate_file_info(file_path, file_data)
            directory_files[file_path.name] = file_info

        return directory_files

    def copy_to(self, destination_path):
        """
        Copies the source role directory to a given destination.

        Args:
            destination_path (str): destination path
        """
        destination = Path(destination_path) / self.name
        if destination.exists():
            shutil.rmtree(destination)

    def symlink_to(self, destination_path):
        """
        Symlinks the source role directory to a given destination.

        Args:
            destination_path (str): destination path
        """
        destination = Path(destination_path) / self.name
        if destination.exists():
            destination.unlink()
        destination.symlink_to(self.path)
