"""
This module contains the AnsibleDeployment skeleton class.
"""

import json
from inspect import isclass
from pathlib import Path
from ansible_deployment.config import DEFAULT_OUTPUT_JSON_INDENT


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder.
    """
    def default(self, o):
        """
        Encode object to json.

        Args:
            o (any): Object to encode.

        Returns:
            str: Encoded json.
        """
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

    Attributes:
        name (str): Class name.
        filtered_attributes (list): Attributes filtered in representation.
        filtered_values (list): Values filtered in representation.
        filtered_representation (dict): If defined, will override default representation.
    """

    filtered_attributes = ["config"]
    filtered_values = []
    filtered_representation = None
    name = "ansible_deployment_object"


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
        if self.filtered_representation is not None:
            representation = self.filtered_representation
        else:
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
        """
        Wrapper for `self.name.startswith()`.

        Args:
            substring: Substring to match against.

        Returns:
            bool: Whether or not a match was found.
        """
        return self.name.startswith(substring)
