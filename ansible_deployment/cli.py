import click
from pathlib import Path, PosixPath
from pprint import pformat
from ansible_deployment import Deployment, cli_helpers

deployment_path = Path.cwd()
deployment_config_path = Path.cwd() / 'deployment.json'


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

    deployment = Deployment.load(deployment_config_path)

    if not deployment:
        cli_helpers.err_exit("Deployment initialization failed.")

    ctx.invoke(show)
    if click.confirm('(Re)Initialize Deployment?'):
        deployment.initialize_deployment_directory()
        deployment.save()


@cli.command()
@click.argument('attribute', required=False, nargs=-1)
def show(attribute):
    """
    Show deployment information. 

    Deployment information may be filtered by specifying attribute(s).
    """
    deployment = Deployment.load(deployment_config_path)
    output = deployment
    if attribute:
        output = cli_helpers.filter_output_by_attribute(output, attribute)
    click.echo(pformat(output))


@cli.command()
@click.argument('role', required=False, nargs=-1)
def run(role):
    """
    Run deployment with ansible-playbook.

    This will create a commit in the deployment repository
    containing the executed command.
    """
    deployment = Deployment.load(deployment_config_path)
    if deployment.deployment_dir.repo.is_dirty():
        cli_helpers.err_exit('Deployment repo has to be clean.')
    deployment.run(role)


@cli.command()
@click.pass_context
def delete(ctx):
    """
    Delete deployment.

    Deletes all created files and directories in deployment directory.
    """
    deployment = Deployment.load(deployment_config_path)
    ctx.invoke(show)
    if click.confirm('Delete deployment?'):
        deployment.deployment_dir.delete()


@cli.command()
@click.argument('host')
def ssh(host):
    """
    Run 'ssh' command to connect to a inventory host.
    """
    deployment = Deployment.load(deployment_config_path)
    deployment.ssh(host)


@cli.command(help='Update deployment roles.')
def update():
    """
    Updates all deployment files and directories.

    This will pull new changes from the roles source repository and
    update all deployment files accordingly.
    All changes will be shown as diff and the user needs to decide a.
    update strategy.
    """

    deployment = Deployment.load(deployment_config_path)
    cli_helpers.check_environment(deployment)
    deployment.update()
    files_to_commit = cli_helpers.prompt_for_update_choices(
        deployment.deployment_dir)
    deployment.deployment_dir.update_git(files=files_to_commit)


def main():
    cli(auto_envvar_prefix='AD')


if __name__ == '__main__':
    main()
