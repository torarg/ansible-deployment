"""
ansible-deployment config module.
"""
import json
from pathlib import Path
from collections import namedtuple
from ansible_deployment.exceptions import DeploymentConfigNotFound

DEFAULT_DEPLOYMENT_PATH = Path.cwd()
DEFAULT_DEPLOYMENT_CONFIG_PATH = Path.cwd() / "deployment.json"
DEFAULT_OUTPUT_JSON_INDENT = 2

RepoConfig = namedtuple("RepoConfig", "url reference")
"""
Represents a remote git repository configuration.

Args:
    url (str): A clonable git repository url.
    reference (str): Git reference to checkout.
"""

DeploymentConfig = namedtuple(
    "DeploymentConfig",
    "name deployment_repo roles_repo roles inventory_sources inventory_writers",
)
"""
Represents the deployment configuration.

Inventory sources are queried in the order specified and produce a
merged inventory in which the last specified inventory source may
overwrite earlier queried values.

Inventory writers persist the current inventory at another location.

Args:
    name (String): Deployment name
    deployment_repo (RepoConfig): Namedtuple containing deployment repo information.
    roles_repo (RepoConfig): Namedtuple containing roles repo information.
    roles (sequence): A sequence of role names.
    inventory_sources (sequence): Sequence of inventory plugin names.
    inventory_writers (sequence): Sequence of inventory plugin names.
"""

def parse_repo_config(raw_repo_config):
    """
    Parses json repo configuration.

    Args:
        raw_repo_config (dict): json repo configuration.
    Returns:
        RepoConfig: Parsed repo config as namedtuple.
    """

    repo_config = RepoConfig(
        raw_repo_config["url"], raw_repo_config["reference"]
    )
    return repo_config


def load_config_file(config_file_path):
    """
    Loads deployment configuration from json file.

    Args:
        config_file_path (path): Path to config file.

    Returns:
        DeploymentConfig: Namedtuple containing deployment config.
    """
    if not config_file_path.exists():
        raise DeploymentConfigNotFound(config_file_path)
    with open(config_file_path) as config_file_stream:
        config = json.load(config_file_stream)
    config["deployment_repo"] = parse_repo_config(config['deployment_repo'])
    config["roles_repo"] = parse_repo_config(config['roles_repo'])

    return DeploymentConfig(**config)
