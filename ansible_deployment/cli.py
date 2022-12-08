import click
from pathlib import Path, PosixPath
from pprint import pprint
from ansible_deployment.deployment import Deployment, load_deployment


@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
#@click.argument('playbook_name', required=True)
@click.option('--role', '-r', 'roles', multiple=True, required=True)
@click.option('--ansible_roles_dir', required=True)
@click.option('--inventory', '-i', 'inventory_type', required=True)
def init(roles, ansible_roles_dir, inventory_type):
    ansible_roles_path = Path(ansible_roles_dir)
    deployment_path = Path.cwd()
    deployment = Deployment(deployment_path, ansible_roles_path, roles, inventory_type)
    deployment.initialize_deployment_directory()
    deployment.save()

@cli.command()
@click.argument('attribute', required=False)
def show(attribute):
    deployment_state_path = Path.cwd() / '.deployment.state'
    deployment = load_deployment()
    print_types = (str, list, PosixPath)
    if attribute:
        if type(deployment.__dict__[attribute]) in print_types:
            pprint(deployment.__dict__[attribute])
        else:
            pprint(deployment.__dict__[attribute].__dict__)
    else:
        pprint(deployment.__dict__)

@cli.command()
def run():
    deployment_state_path = Path.cwd() / '.deployment.state'
    deployment = load_deployment()
    deployment.run()

@cli.command()
def delete():
    deployment_state_path = Path.cwd() / '.deployment.state'
    deployment = load_deployment()
    deployment.delete()

@cli.command()
@click.argument('host')
def ssh(host):
    deployment_state_path = Path.cwd() / '.deployment.state'
    deployment = load_deployment()
    deployment.ssh(host)
    

def main():
    cli(auto_envvar_prefix='AD')

if __name__ == '__main__':
    main()
