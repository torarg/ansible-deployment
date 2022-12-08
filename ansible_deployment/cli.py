"""
This module represents the ansible-deployment cli.
"""

from pathlib import Path
from pprint import pformat
import click
import subprocess
from ansible_deployment import Deployment, cli_helpers, unlock_deployment, lock_deployment

deployment_path = Path.cwd()
deployment_config_path = Path.cwd() / "deployment.json"


@click.group()
@click.version_option()
@click.pass_context
@click.option("--debug", is_flag=True, help="Enable debug output.")
def cli(ctx, debug):
    """
    All available commands are listed below.

    Each command has it's own help that can be shown by passing '--help':

        $ ansible-deployment COMMAND --help
    """
    try:
        deployment = Deployment.load(deployment_config_path)
    except Exception as err:
        if debug:
            raise
        else:
            raise click.ClickException(err)

    if not deployment:
        cli_helpers.err_exit("Deployment initialization failed.")

    if deployment.deployment_dir.vault.new_key:
        new_key_message = click.style(
            "Deployment key written to: {}".format(
                deployment.deployment_dir.vault.key_file
            ),
            fg="red",
            bold=True,
        )
        click.echo(new_key_message)
    ctx.ensure_object(dict)
    ctx.obj["DEPLOYMENT"] = deployment
    ctx.obj["DEBUG"] = debug


@cli.command()
@click.pass_context
@click.option(
    "--non-interactive", is_flag=True, help="Don't ask before initializing deployment."
)
def init(ctx, non_interactive):
    """
    Initialize deployment directory.

    Initialization requires a 'deployment.json' file in the
    current working directory.
    """

    try:
        deployment = Deployment.load(deployment_config_path, read_sources=True)
    except Exception as err:
        if ctx.obj['DEBUG']:
            raise
        else:
            raise click.ClickException(err)

    if non_interactive:
        deployment.deployment_dir.delete()
        deployment.initialize_deployment_directory()
    else:
        ctx.invoke(show)
        if click.confirm("(Re)Initialize Deployment?"):
            deployment.deployment_dir.delete()
            deployment.initialize_deployment_directory()


@cli.command()
@click.pass_context
@click.argument("attribute", required=False, nargs=-1)
def show(ctx, attribute):
    """
    Show deployment information.

    Deployment information may be filtered by specifying attribute(s).
    """
    with unlock_deployment(ctx.obj["DEPLOYMENT"], 'r') as deployment:
        output = deployment
        if attribute:
            output = cli_helpers.filter_output_by_attribute(output, attribute)
        click.echo(pformat(output))


@cli.command()
@click.pass_context
@click.option(
    "-l", "--limit", help="Limit playbook execution."
)
@click.option(
    "-e", "--extra-var", help="Set extra var for playbook execution.", multiple=True
)
@click.argument("role", required=False, nargs=-1)
def run(ctx, role, limit, extra_var):
    """
    Run deployment with ansible-playbook.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'r') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment)
            unlocked_deployment.run(role, limit=limit, extra_vars=extra_var)
    except Exception as err:
        raise click.ClickException(err)


@cli.command()
@click.pass_context
@click.option(
    "--non-interactive", is_flag=True, help="Don't ask before deleting deployment."
)
def delete(ctx, non_interactive):
    """
    Delete deployment.

    Deletes all created files and directories in deployment directory.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    if non_interactive:
        deployment.inventory.delete_from_writers()
        deployment.deployment_dir.delete(full_delete=True)
    else:
        ctx.invoke(show)
        if click.confirm("Delete deployment?"):
            deployment.inventory.delete_from_writers()
            deployment.deployment_dir.delete(full_delete=True)


@cli.command()
@click.pass_context
def lock(ctx):
    """
    Encrypt all deployment files except the roles directory.
    """
    try:
        deployment = Deployment.load(deployment_config_path, read_sources=False)
    except Exception as err:
        if ctx.obj['DEBUG']:
            raise
        else:
            raise click.ClickException(err)
    if deployment.deployment_dir.vault.locked:
        cli_helpers.err_exit("Deployment already locked")
    cli_helpers.check_environment(deployment)
    prompt = "Encrypt deployment with {}?".format(
        deployment.deployment_dir.vault.key_file
    )
    if click.confirm(prompt):
        deployment.deployment_dir.vault.lock()
        deployment.inventory.plugin.delete_added_files()
        deployment.deployment_dir.delete(keep=['.git'])
        deployment.deployment_dir.vault.setup_shadow_repo(remote_config=deployment.config.deployment_repo)


@cli.command()
@click.option(
    "--force", is_flag=True, help="Unlock even if deployment verification failed."
)
@click.pass_context
def unlock(ctx, force):
    """
    Decrypt all deployment files except the roles directory.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    if not deployment.deployment_dir.vault.locked:
        cli_helpers.err_exit("Deployment already unlocked")
    prompt = "Decrypt deployment with {}?".format(
        deployment.deployment_dir.vault.key_file
    )
    if click.confirm(prompt):
        deployment.deployment_dir.vault.unlock(force)
        deployment.deployment_dir.vault.delete()
        deployment = Deployment.load(deployment_config_path)


@cli.command()
@click.pass_context
@click.argument("host")
def ssh(ctx, host):
    """
    Run 'ssh' command to connect to a inventory host.
    """
    try:
        with unlock_deployment(ctx.obj["DEPLOYMENT"], 'r') as deployment:
            deployment.ssh(host)
    except Exception as err:
        if ctx.obj["DEBUG"]:
            raise
        else:
            raise click.ClickException(err)


@cli.command(hidden=True)
@click.option('--template-mode', is_flag=True,
              help='Run inventory writers without ssh and deployment keys.')
@click.pass_context
def push(ctx, template_mode=False):
    """
    Run configured ìnventory_writers and push encrypted git repo.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    with unlock_deployment(deployment, 'r') as unlocked_deployment:
        cli_helpers.check_environment(unlocked_deployment)
        if unlocked_deployment.inventory.loaded_writers:
            try:
                unlocked_deployment.inventory.run_writer_plugins(template_mode)
            except Exception as err:
                if ctx.obj["DEBUG"]:
                    raise
                else:
                    raise click.ClickException(err)

    deployment = Deployment(deployment.deployment_dir.path, deployment.config)
    with lock_deployment(deployment) as locked_deployment:
        try:
            locked_deployment.deployment_dir.deployment_repo.push()
        except Exception as err:
            if ctx.obj["DEBUG"]:
                raise
            else:
                raise click.ClickException(err)


@cli.command()
@click.pass_context
def pull(ctx):
    """
    Pull encrypted deployment repo.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    with lock_deployment(deployment) as locked_deployment:
        blobs = { "deployment_data": "./deployment.tar.gz.enc" }
        try:
            locked_deployment.deployment_dir.delete(keep=['.git'])
            locked_deployment.deployment_dir.deployment_repo.pull(blobs=blobs)
        except Exception as err:
            if ctx.obj["DEBUG"]:
                raise
            else:
                raise click.ClickException(err)


@cli.command()
@click.pass_context
@click.option(
    "--non-interactive", is_flag=True, help="Apply all updates without asking."
)
@click.option(
    "-s", "--source", help="Override configured inventory source.", multiple=True
)
def update(ctx, non_interactive, source):
    """
    Update deployment.

    Updates deployment inventory from inventory_sources and pulls changes
    from roles repository.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    with unlock_deployment(deployment) as unlocked_deployment:
        try:
            cli_helpers.update_deployment(unlocked_deployment, 'all', 
                non_interactive, sources_override=source)
        except Exception as err:
            if ctx.obj["DEBUG"]:
                raise
            else:
                raise click.ClickException(err)



@cli.command()
@click.pass_context
def edit(ctx):
    """
    Edit deployment with vim.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'w') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment)
            subprocess.run(["vim", "."], check=True)
    except Exception as err:
        raise click.ClickException(err)

@cli.command()
@click.pass_context
def commit(ctx):
    """
    Commit all changes.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'w') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment, ignore_dirty_repo=True)
            subprocess.run(["git", "commit", "-a"], check=True)
    except Exception as err:
        raise click.ClickException(err)

@cli.command()
@click.pass_context
def log(ctx):
    """
    Show deployment log.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'r') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment, ignore_dirty_repo=True)
            subprocess.run(["git", "log"], check=True)
    except Exception as err:
        raise click.ClickException(err)

@cli.command()
@click.pass_context
def diff(ctx):
    """
    Show deployment diff.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'r') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment, ignore_dirty_repo=True)
            subprocess.run(["git", "diff"], check=True)
    except Exception as err:
        raise click.ClickException(err)

@cli.command()
@click.pass_context
def reset(ctx):
    """
    Hard reset deployment to last commit.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'w') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment, ignore_dirty_repo=True)
            subprocess.run(["git", "reset", "--hard"], check=True)
    except Exception as err:
        raise click.ClickException(err)

@cli.command()
@click.pass_context
def update_known_hosts(ctx):
    """
    Force update of known_hosts file.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'w') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment, ignore_dirty_repo=True)
            deployment.update_known_hosts()
    except Exception as err:
        raise click.ClickException(err)

@cli.command()
@click.pass_context
@click.argument("inventory_source")
def fetch_key(ctx, inventory_source):
    """
    Fetch deployment key from given inventory source.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    deployment.fetch_key(inventory_source)

def main():
    """
    This function is only used to set 'auto_envvars_prefix'.
    """
    cli(auto_envvar_prefix="AD")


if __name__ == "__main__":
    main()
