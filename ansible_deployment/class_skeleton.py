from pprint import pformat


class AnsibleDeployment:
    """
    Represents the skeleton for all ansible_deployment classes.

    The main purpose of this claass is to provide lookup and representation methods.
    """
    filtered_attributes = ['config']
    filtered_values = ['playbook', 'inventory', 'deployment_dir']

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

        representation = {}
        for attribute in self.__dict__:
            if attribute in self.filtered_attributes:
                continue
            elif attribute in self.filtered_values:
                representation[attribute] = "filtered"
            else:
                representation[attribute] = self.__dict__[attribute]
        return pformat(representation, indent=4)
