"""
This module represents the ansible-deployment cli.
"""

from pathlib import Path
from pprint import pformat
import click
from ansible_deployment import Deployment, cli_helpers

deployment_path = Path.cwd()
deployment_config_path = Path.cwd() / 'deployment.json'


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    try:
        deployment = Deployment.load(deployment_config_path)
    except Exception as err:
        raise click.ClickException(err)

    if not deployment:
        cli_helpers.err_exit("Deployment initialization failed.")

    if deployment.deployment_dir.vault.new_key:
        new_key_message = click.style('New key generated: {}'.format(
            deployment.deployment_dir.vault.key_file),
                                      fg='red',
                                      bold=True)
        click.echo(new_key_message)
    ctx.ensure_object(dict)
    ctx.obj['DEPLOYMENT'] = deployment


@cli.command()
@click.pass_context
@click.option('--non-interactive', is_flag=True, help="Don't ask before initializing deployment.")
def init(ctx, non_interactive):
    """
    Initialize deployment directory.

    Initialization requires a 'deployment.json' file in the
    current working directory.
    """

    deployment = ctx.obj['DEPLOYMENT']

    if non_interactive:
        deployment.initialize_deployment_directory()
        deployment.inventory.run_writer_plugins()
    else:
        ctx.invoke(show)
        if click.confirm('(Re)Initialize Deployment?'):
            deployment.initialize_deployment_directory()
            deployment.inventory.run_writer_plugins()


@cli.command()
@click.pass_context
@click.argument('attribute', required=False, nargs=-1)
def show(ctx, attribute):
    """
    Show deployment information.

    Deployment information may be filtered by specifying attribute(s).
    """
    deployment = ctx.obj['DEPLOYMENT']
    output = deployment
    if attribute:
        output = cli_helpers.filter_output_by_attribute(output, attribute)
    click.echo(pformat(output))


@cli.command()
@click.pass_context
@click.argument('role', required=False, nargs=-1)
def run(ctx, role):
    """
    Run deployment with ansible-playbook.

    This will create a commit in the deployment repository
    containing the executed command.
    """
    deployment = ctx.obj['DEPLOYMENT']
    cli_helpers.check_environment(deployment)
    try:
        deployment.run(role)
    except Exception as err:
        raise click.ClickException(err)


@cli.command()
@click.pass_context
@click.option('--non-interactive', is_flag=True, help="Don't ask before deleting deployment.")
def delete(ctx, non_interactive):
    """
    Delete deployment.

    Deletes all created files and directories in deployment directory.
    """
    deployment = ctx.obj['DEPLOYMENT']
    if non_interactive:
        deployment.deployment_dir.delete()
    else:
        ctx.invoke(show)
        if click.confirm('Delete deployment?'):
            deployment.deployment_dir.delete()


@cli.command()
@click.pass_context
def lock(ctx):
    """
    Encrypt all deployment files except the roles directory.
    """
    deployment = ctx.obj['DEPLOYMENT']
    cli_helpers.check_environment(deployment)
    prompt = "Encrypt deployment with {}?".format(
        deployment.deployment_dir.vault.key_file)
    if click.confirm(prompt):
        deployment.deployment_dir.deployment_repo.update(
            message='deployment was locked', force_commit=True)
        deployment.deployment_dir.vault.lock()


@cli.command()
@click.pass_context
def unlock(ctx):
    """
    Decrypt all deployment files except the roles directory.
    """
    deployment = ctx.obj['DEPLOYMENT']
    prompt = "Decrypt deployment with {}?".format(
        deployment.deployment_dir.vault.key_file)
    if click.confirm(prompt):
        deployment.deployment_dir.vault.unlock()
        deployment = Deployment.load(deployment_config_path)
        deployment.deployment_dir.deployment_repo.update(
            message='deployment was unlocked', force_commit=True)


@cli.command()
@click.pass_context
@click.argument('host')
def ssh(ctx, host):
    """
    Run 'ssh' command to connect to a inventory host.
    """
    deployment = ctx.obj['DEPLOYMENT']
    deployment.ssh(host)


@cli.command()
@click.pass_context
@click.argument('scope',
                type=click.Choice(('all', 'playbook', 'roles', 'inventory',
                                   'group_vars', 'ansible_cfg')),
                required=False,
                default='all')
@click.option('--non-interactive', is_flag=True, help="Apply all updates without asking.")
def update(ctx, scope, non_interactive):
    """
    Updates all deployment files and directories.

    This will pull new changes from the roles source repository and
    update all deployment files accordingly.
    All changes will be shown as diff and the user needs to decide a.
    update strategy.

    The update can be restricted in scope by specifying the SCOPE argument.

    Args:
        scope (str): Update scope. Defaults to 'all'.
    """

    deployment = ctx.obj['DEPLOYMENT']
    cli_helpers.check_environment(deployment)
    deployment.deployment_dir.update(deployment, scope)
    if non_interactive:
        files_to_commit = deployment.deployment_dir.deployment_repo.changes['all']
    else:
        files_to_commit = cli_helpers.prompt_for_update_choices(
            deployment.deployment_dir)
    files_to_commit += deployment.deployment_dir.deployment_repo.changes['new']
    commit_message = "deployment update with scope: {}".format(scope)
    if deployment.deployment_dir.deployment_repo.changes['new']:
        click.echo(f"New files: {deployment.deployment_dir.deployment_repo.changes['new']}")
    deployment.deployment_dir.deployment_repo.update(files=files_to_commit,
                                                     message=commit_message)
    deployment.inventory.run_writer_plugins()


def main():
    """
    This function is only used to set ``auto_envvars_prefix``
    """
    cli(auto_envvar_prefix='AD')


if __name__ == '__main__':
    main()
