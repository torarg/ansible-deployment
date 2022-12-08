"""
Custom click.ParamType classes for shell completion.
"""


import click
import inspect
from click import ParamType
from click.shell_completion import CompletionItem
from ansible_deployment import Deployment
from ansible_deployment.cli_helpers import filter_output_by_attribute
from ansible_deployment.config import DEFAULT_DEPLOYMENT_CONFIG_PATH
from ansible_deployment.exceptions import DeploymentConfigNotFound
from ansible_deployment.class_skeleton import AnsibleDeployment


class CustomParamType(ParamType):
    """
    Custom ParamType parent class for ansible-deployment cli parameters.
    """
    name = "custom_parameter"
    @staticmethod
    def try_to_load_deployment():
        """
        Tries to load deployment and will return None if it fails.

        Args:
            deployment_config_path (pathlib.Path): Path to deployment config.

        Returns:
            Deployment: initialized deployment or None if errors occcured.
        """
        deployment = None
        try:
            deployment = Deployment.load(DEFAULT_DEPLOYMENT_CONFIG_PATH)
        except:
            pass
        return deployment


class RoleType(CustomParamType):
    """
    Custom ParamType for `Role` objects.
    """
    name = "role"

    def shell_complete(self, ctx, param, incomplete):
        deployment = self.try_to_load_deployment()
        if deployment is None:
            return []
        roles = deployment.roles
        return [
            CompletionItem(role.group_name)
            for role in roles if role.group_name.startswith(incomplete)
        ]


class HostType(CustomParamType):
    """
    Custom ParamType for `Host` objects.
    """
    name = "host"

    def shell_complete(self, ctx, param, incomplete):
        deployment = self.try_to_load_deployment()
        if deployment is None:
            return []
        hosts = deployment.inventory.host_vars.keys()
        return [
            CompletionItem(host)
            for host in hosts if host.startswith(incomplete)
        ]


class InventoryWriterType(CustomParamType):
    """
    Custom ParamType for `InventoryWriter` objects.
    """
    name = "inventory_writer"

    def shell_complete(self, ctx, param, incomplete):
        deployment = self.try_to_load_deployment()
        if deployment is None:
            return []
        writers = deployment.config.inventory_writers
        return [
            CompletionItem(writer)
            for writer in writers if writer.startswith(incomplete)
        ]


class InventorySourceType(CustomParamType):
    """
    Custom ParamType for `InventorySource` objects.
    """
    name = "inventory_source"

    def shell_complete(self, ctx, param, incomplete):
        deployment = self.try_to_load_deployment()
        if deployment is None:
            return []
        sources = deployment.config.inventory_sources + ["local"]
        return [
            CompletionItem(source)
            for source in sources if source.startswith(incomplete)
        ]


class GroupVarsType(CustomParamType):
    """
    Custom ParamType for `group_vars`.
    """
    name = "group_vars"

    def shell_complete(self, ctx, param, incomplete):
        deployment = self.try_to_load_deployment()
        if deployment is None:
            return []
        group_vars = []
        for group, variables in deployment.inventory.group_vars.items():
            group_vars += list(variables.keys())
        group_vars = [ f"{var_name}=" for var_name in group_vars ]
        return [
            CompletionItem(var_name)
            for var_name in group_vars if var_name.startswith(incomplete)
        ]


class ShowAttributeType(CustomParamType):
    """
    Custom ParamType for any given attribute for `show` subcommand.
    """
    name = "show_attribute"

    def shell_complete(self, ctx, param, incomplete):
        result = []
        deployment = self.try_to_load_deployment()
        if deployment is None:
            return []
        output = deployment.__dict__
        if len(ctx.params['attribute']) > 0:
            try:
                output = filter_output_by_attribute(output, ctx.params['attribute'])
                if type(output) not in (str, list, tuple, dict):
                    output = output.__dict__
            except:
                return []
        if type(output) is str:
            return []
        for entry in output:
            if entry.startswith(incomplete):
                if type(entry) is str:
                    result.append(CompletionItem(entry))
                else:
                    result.append(CompletionItem(entry.name))
        return result
