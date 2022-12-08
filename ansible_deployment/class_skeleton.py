"""
This module contains the AnsibleDeployment skeleton class.
"""

import json
from inspect import isclass
from pathlib import Path
from ansible_deployment.config import DEFAULT_OUTPUT_JSON_INDENT


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        result = None
        if type(o) is dict:
            result = o
        elif isinstance(o, AnsibleDeployment):
            result = o._get_filtered_dict()
        else:
            result = str(o)
        return result


class AnsibleDeployment:
    """
    Represents the skeleton for all ansible_deployment classes.

    The main purpose of this class is to provide 'magic methods'
    for object lookup and representation.
    """

    filtered_attributes = ["config", "playbook"]
    filtered_values = ["playbook", "inventory", "deployment_dir"]

    def __init__(self):
        self.filtered_representation = "filtered"
        self.name = "AnsibleDeployment Object"

    def __getitem__(self, attribute):
        """
        Lookup a given attribute in self.__dict__.

        Args:
            attribute (str): Attribute to look up.
        Returns:
            Value of attribute.
        """
        return self.__dict__[attribute]

    def __contains__(self, attribute):
        """
        Check if attribute is in self.__dict__.

        Args:
            attribute (str): Atrribute to check

        Returns:
            bool: True if attribute is in self.__dict__.
        """

        return attribute in self.__dict__

    def __repr__(self):
        """
        Returns object representation.

        The object representation may be modified by the object's variables
        `self.filtered_attributes` and `self.filtered_values`.

        Returns:
            str: Formatted and filtered object representation.
        """
        representation = self._get_filtered_dict()
        return json.dumps(representation, indent=DEFAULT_OUTPUT_JSON_INDENT,
                          cls=CustomJSONEncoder)

    def _get_filtered_dict(self):
        representation = {}
        for attribute, attr_obj in self.__dict__.items():
            if attribute in self.filtered_attributes:
                continue
            if attribute in self.filtered_values:
                representation[attribute] = attr_obj[
                    "filtered_representation"
                ]
            elif attribute == "roles":
                representation[attribute] = [
                    role["name"] for role in self.__dict__["roles"]
                ]
            else:
                representation[attribute] = attr_obj
        return representation

    def startswith(self, substring):
        return self.name.startswith(substring)
