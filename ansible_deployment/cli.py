import sys
import click
import json
from pathlib import Path, PosixPath
from pprint import pformat
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
    custom_types = (Deployment, Playbook, Role, Inventory)
    if attribute and attribute in deployment.__dict__:
        click.echo(pformat(deployment.__dict__[attribute]))
    else:
        click.echo(pformat(deployment))


@cli.command(help='Run deployment with ansible-playbook.')
@click.argument('role', required=False)
def run(role):
    deployment = Deployment.load(deployment_state_path)
    deployment.run(role)


@cli.command(help='Delete deployment.')
@click.pass_context
def delete(ctx):
    deployment = Deployment.load(deployment_state_path)
    ctx.invoke(show)
    if click.confirm('Delete deployment?'):
        deployment.deployment_dir.delete()


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
    click.echo(deployment.deployment_dir.repo.git.diff())
    update_choice = click.prompt(
        'Please select update strategy',
        default='keep_unstaged',
        type=click.Choice(['commit', 'keep_unstaged', 'discard'])
    )
    if update_choice == 'commit':
        deployment.deployment_dir.update_git()
    elif update_choice == 'discard':
        deployment.deployment_dir.repo.git.reset('--hard')


def err_exit(error_message):
    cli_context = click.get_current_context()
    cli_context.fail(error_message)


def main():
    cli(auto_envvar_prefix='AD')


if __name__ == '__main__':
    main()
