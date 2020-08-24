import sys
import click
import json
from pathlib import Path, PosixPath
from pprint import pprint
from ansible_deployment.deployment import Deployment
from ansible_deployment.playbook import Playbook
from ansible_deployment.role import Role
from ansible_deployment.inventory import Inventory

deployment_path = Path.cwd()
deployment_state_path = Path.cwd() / 'deployment.json'

@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
def init():
    """
    Initialize deployment directory.

    Initialization requires a 'deployment.json' file in the
    current working directory.
    """

    ansible_roles_src = {
        'repo': None,
        'branch': None 
    }

    deployment = Deployment.load(deployment_state_path)

    if not deployment:
        err_exit("Deployment initialization failed.")

    deployment.initialize_deployment_directory()
    deployment.save()

@cli.command(help='Show deployment information.')
@click.argument('attribute', required=False)
def show(attribute):
    deployment = Deployment.load(deployment_state_path)
    dict_types = (Deployment, Playbook, Role, Inventory, dict)
    if attribute:
        if not attribute in deployment.__dict__:
            err_exit("Attribute not found.")
        if type(deployment.__dict__[attribute]) in dict_types:
            pprint(deployment.__dict__[attribute].__dict__)
        else:
            pprint(deployment.__dict__[attribute])
    else:
        pprint(deployment.__dict__)

@cli.command(help='Run deployment with ansible-playbook.')
def run():
    deployment = Deployment.load(deployment_state_path)
    deployment.run()

@cli.command(help='Delete deployment.')
def delete():
    deployment = Deployment.load(deployment_state_path)
    deployment.delete()

@cli.command(help='SSH into a given host of deployment inventory.')
@click.argument('host')
def ssh(host):
    deployment = Deployment.load(deployment_state_path)
    deployment.ssh(host)

@cli.command(help='Update deployment roles.')
def update():
    deployment = Deployment.load(deployment_state_path)
    if not deployment:
        err_exit("Failed to load deployment.json")
    deployment.update()
    


def err_exit(error_message):
    cli_context = click.get_current_context()
    cli_context.fail(error_message)

def main():
    cli(auto_envvar_prefix='AD')

if __name__ == '__main__':
    main()
