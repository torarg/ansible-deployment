import click
from click import ParamType
from click.shell_completion import CompletionItem
from ansible_deployment import Deployment


class CustomParamType(ParamType):
    def __init__(self, deployment_config_path):
        self.deployment = None
        if deployment_config_path.exists():
            try:
                self.deployment = Deployment.load(deployment_config_path)
            except:
                pass


class RoleType(CustomParamType):
    name = "role"

    def shell_complete(self, ctx, param, incomplete):
        if self.deployment is None:
            return []
        roles = self.deployment.roles
        return [
            CompletionItem(role.group_name)
            for role in roles if role.group_name.startswith(incomplete)
        ]


class HostType(CustomParamType):
    name = "host"

    def shell_complete(self, ctx, param, incomplete):
        if self.deployment is None:
            return []
        hosts = self.deployment.inventory.filtered_representation
        return [
            CompletionItem(host)
            for host in hosts if host.startswith(incomplete)
        ]


class InventoryWriterType(CustomParamType):
    name = "inventory_writer"

    def shell_complete(self, ctx, param, incomplete):
        if self.deployment is None:
            return []
        writers = self.deployment.config.inventory_writers
        return [
            CompletionItem(writer)
            for writer in writers if writer.startswith(incomplete)
        ]


class InventorySourceType(CustomParamType):
    name = "inventory_source"

    def shell_complete(self, ctx, param, incomplete):
        if self.deployment is None:
            return []
        sources = self.deployment.config.inventory_sources
        return [
            CompletionItem(source)
            for source in sources if source.startswith(incomplete)
        ]
