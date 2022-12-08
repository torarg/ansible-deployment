class DeploymentConfigNotFound(Exception):
    """
    Exception raised when deployment config doesn't exist.

    Attributes:
        config_file_path (pathlib.Path): Config file that was attempted to laod.
        message (str): Exception message
    """
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.message = f"{self.config_file_path} does not exist."
        super().__init__(self.message) 
        
