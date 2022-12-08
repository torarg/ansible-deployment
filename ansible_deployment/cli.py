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


@cli.command(help='Initialize deployment directory.')
@click.option('--role', '-r', 'roles', multiple=True, 
              help="""Role(s) to include in deployment.
                      May be specified multiple times.""")
@click.option('--ansible_roles',
              help='Clonable git repo containing ansible roles.')
@click.option('--branch', '-b',
              help='Branch to checkout from ansible roles repo.')
@click.option('--inventory', '-i', 'inventory_type', 
              help='Inventory type. Supported: terraform, static')
def init(roles, ansible_roles, branch, inventory_type):
    ansible_roles_src = {
        'repo': ansible_roles,
        'branch': branch
    }

    required_args = (roles, ansible_roles, branch, inventory_type)
    if all(required_args):
        deployment = Deployment(deployment_path, ansible_roles_src, roles, inventory_type)
    else:
        deployment = Deployment.load(deployment_state_path)

    if not deployment:
        err_exit("Deployment initialization failed.")

    deployment.initialize_deployment_directory()
    deployment.save()

@cli.command(help='Show deployment information.')
@click.argument('attribute', required=False)
def show(attribute):
    deployment = Deployment.load(deployment_state_path)
    dict_types = (Deployment, Playbook, Role, Inventory, dict, list)
    if attribute:
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
    deployment.update()
    


def err_exit(error_message):
    print("Error: {}".format(error_message))
    sys.exit(1)

def main():
    cli(auto_envvar_prefix='AD')

if __name__ == '__main__':
    main()
