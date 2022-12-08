"""
This module contains custom Exception classes.
"""


class DeploymentConfigNotFound(Exception):
    """
    Exception raised when deployment config doesn't exist.

    Attributes:
        config_file_path (pathlib.Path): Config file that was attempted to laod.
        message (str): Exception message
    """
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.message = f"Deployment config ({self.config_file_path}) doesn't exist."
        super().__init__(self.message)


class AttributeNotFound(Exception):
    """
    Exception raised when an deployment attribute doesn't exist.

    Attributes:
        attribute (str): Attribute tried to lookup.
        message (str): Exception message
    """
    def __init__(self, attribute):
        self.attribute = attribute
        self.message = f"Deployment attrbute ({self.attribute}) doesn't exist."
        super().__init__(self.message)


class NotSupportedByPlugin(Exception):
    """
    Exception raised when an unsupported plugin operation is requested.

    Attributes:
        attribute (str): Attribute tried to lookup.
        message (str): Exception message
    """
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.message = f"Operation not supported by plugin ({self.plugin_name})."
        super().__init__(self.message)
