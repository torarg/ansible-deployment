"""
ansible-deployment config module.
"""
import json
from collections import namedtuple


RepoConfig = namedtuple("RepoConfig", "repo branch")
"""
Represents a remote git repository configuration.

Args:
    repo (str): A clonable git repository path or url.
    branch (str): Git branch to checkout.
"""

DeploymentConfig = namedtuple(
    "DeploymentConfig",
    "name roles roles_src inventory_sources inventory_writers",
)
"""
Represents the deployment configuration.

Inventory sources are queried in the order specified and produce a
merged inventory in which the last specified inventory source may
overwrite earlier queried values.

Inventory writers persist the current inventory at another location.

Args:
    name (String): Deployment name
    roles (sequence): A sequence of role names.
    roles_src (RepoConfig): Namedtuple containing roles repo information.
    inventory_sources (sequence): Sequence of inventory plugin names.
    inventory_writers (sequence): Sequence of inventory plugin names.
"""

def load_config_file(config_file_path):
    """
    Loads deployment configuration from json file.

    Args:
        config_file_path (path): Path to config file.

    Returns:
        DeploymentConfig: Namedtuple containing deployment config.
    """
    with open(config_file_path) as config_file_stream:
        config = json.load(config_file_stream)
    roles_src = RepoConfig(
        config["roles_src"]["repo"], config["roles_src"]["branch"]
    )
    config["roles_src"] = roles_src

    return DeploymentConfig(**config)
