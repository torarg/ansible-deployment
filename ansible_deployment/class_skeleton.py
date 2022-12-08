from pprint import pformat

class AnsibleDeployment:
    filtered_attributes = []
    filtered_values = []
    def __getitem__(self, attribute):
        return self.__dict__[attribute]

    def __contains__(self, attribute):
        return attribute in self.__dict__

    def __repr__(self):
        representation = {}
        for attribute in self.__dict__:
            if attribute in self.filtered_attributes:
                continue
            elif attribute in self.filtered_values:
                representation[attribute] = "filtered"
            else:
                representation[attribute] = self.__dict__[attribute]
        return pformat(representation, indent=4)
