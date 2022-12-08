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
@click.pass_context
def init(ctx):
    """
    Initialize deployment directory.

    Initialization requires a 'deployment.json' file in the
    current working directory.
    """

    ansible_roles_src = {'repo': None, 'branch': None}

    deployment = Deployment.load(deployment_state_path)

    if not deployment:
        err_exit("Deployment initialization failed.")

    ctx.invoke(show)
    if click.confirm('(Re)Initialize Deployment?'):
        deployment.initialize_deployment_directory()
        deployment.save()


@cli.command(help='Show deployment information.')
@click.argument('attribute', required=False, nargs=-1)
def show(attribute):
    deployment = Deployment.load(deployment_state_path)
    output = deployment
    custom_types = (Deployment, Playbook, Role, Inventory)
    if attribute:
        for attr in attribute:
            if attr not in output:
                err_exit('Attribute not found')
            output = output[attr]
    click.echo(pformat(output))


@cli.command(help='Run deployment with ansible-playbook.')
@click.argument('role', required=False, nargs=-1)
def run(role):
    deployment = Deployment.load(deployment_state_path)
    if deployment.deployment_dir.repo.is_dirty():
        err_exit('Deployment repo has to be clean.')
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
    files_to_commit = []
    if not deployment:
        err_exit("Failed to load deployment.json")
    elif deployment.deployment_dir.repo.is_dirty():
        err_exit("Repo is dirty. Unstaged changes: {}".format(
            deployment.deployment_dir.unstaged_changes))
    elif not deployment.deployment_dir.roles_path.exists():
        err_exit("Deployment directory not initialized.")
    deployment.update()
    for file_name in deployment.deployment_dir.changes:
        if file_name in deployment.deployment_dir.unstaged_changes:
            click.echo(deployment.deployment_dir.repo.git.diff(file_name))
        elif file_name in deployment.deployment_dir.staged_changes:
            click.echo(deployment.deployment_dir.repo.git.diff('--staged', file_name))
        update_choice = click.prompt(
            'Please select update strategy ([a]pply, [d]iscard, [k]eep unstaged)',
            default='k',
            type=click.Choice(['a', 'd', 'k']),
            show_choices=False)
        if update_choice == 'a':
            files_to_commit.append(file_name)
        elif update_choice == 'd':
            deployment.deployment_dir.repo.git.checkout(file_name)

    deployment.deployment_dir.update_git(files=files_to_commit)


def err_exit(error_message):
    cli_context = click.get_current_context()
    cli_context.fail(error_message)


def main():
    cli(auto_envvar_prefix='AD')


if __name__ == '__main__':
    main()
