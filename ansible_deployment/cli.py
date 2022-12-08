import sys
import click
import json
from pathlib import Path, PosixPath
from pprint import pprint
from ansible_deployment.deployment import Deployment
from ansible_deployment.playbook import Playbook
from ansible_deployment.role import Role
from ansible_deployment.inventory import Inventory


@click.group()
@click.version_option()
def cli():
    pass


@cli.command(help='Initialize deployment directory.')
@click.option('--role', '-r', 'roles', multiple=True, required=True, 
              help="""Role(s) to include in deployment.
                      May be specified multiple times.""")
@click.option('--ansible_roles', required=True,
              help='Path or git url to ansible roles directory.')
@click.option('--inventory', '-i', 'inventory_type', required=True,
              help='Inventory type. Supported: terraform, static')
def init(roles, ansible_roles, inventory_type):
    deployment_path = Path.cwd()
    deployment = Deployment(deployment_path, ansible_roles, roles, inventory_type)
    deployment.initialize_deployment_directory()
    deployment.save()

@cli.command(help='Show deployment information.')
@click.argument('attribute', required=False)
def show(attribute):
    deployment = load_deployment()
    dict_types = (Deployment, Playbook, Role, Inventory, dict)
    if attribute:
        if type(deployment.__dict__[attribute]) in dict_types:
            pprint(deployment.__dict__[attribute].__dict__)
        else:
            pprint(deployment.__dict__[attribute])
    else:
        pprint(deployment.__dict__)

@cli.command(help='Run deployment with ansible-playbook.')
def run():
    deployment = load_deployment()
    deployment.run()

@cli.command(help='Delete deployment.')
def delete():
    deployment = load_deployment()
    deployment.delete()

@cli.command(help='SSH into a given host of deployment inventory.')
@click.argument('host')
def ssh(host):
    deployment = load_deployment()
    deployment.ssh(host)

@cli.command(help='Update deployment roles.')
def update():
    deployment = load_deployment()
    deployment.update()
    

def load_deployment():
    deployment_state_file_path = Path.cwd() / 'deployment.json'
    if deployment_state_file_path.exists():
        with open(deployment_state_file_path) as deployment_state_file_stream:
            deployment_state = json.load(deployment_state_file_stream)
            deployment_path = deployment_state_file_path.parent

        return Deployment(deployment_path,
                          deployment_state['ansible_roles_src'],
                          deployment_state['roles'], 
                          deployment_state['inventory_type'])
    else:
        err_exit('{} does not exist.'.format(deployment_state_file_path))
    return load_deployment()

def err_exit(error_message):
    print("Error: {}".format(error_message))
    sys.exit(1)

def main():
    cli(auto_envvar_prefix='AD')

if __name__ == '__main__':
    main()
