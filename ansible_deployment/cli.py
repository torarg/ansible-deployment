import click
from pathlib import Path
from pprint import pprint
from ansible_deployment.deployment import Deployment
from ansible_deployment.helpers import save_object, load_object

@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
#@click.argument('playbook_name', required=True)
@click.option('--role', '-r', 'roles', multiple=True, required=True)
@click.option('--ansible_roles_dir', required=True)
def init(roles, ansible_roles_dir):
    ansible_roles_path = Path(ansible_roles_dir)
    deployment_path = Path.cwd()
    deployment = Deployment(deployment_path, ansible_roles_path, roles)
    deployment.initialize_deployment_directory()
    save_object(deployment, deployment_path / '.deployment.state')

@cli.command()
def show():
    deployment_state_path = Path.cwd() / '.deployment.state'
    deployment = load_object(deployment_state_path)
    pprint(deployment.__dict__)

@cli.command()
def delete():
    deployment_state_path = Path.cwd() / '.deployment.state'
    deployment = load_object(deployment_state_path)
    deployment.delete()
    

def main():
    cli(auto_envvar_prefix='AD')

if __name__ == '__main__':
    main()
