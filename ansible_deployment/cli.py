"""
This module represents the ansible-deployment cli.
"""

import click
import json
import subprocess
from pygments import highlight, lexers, formatters
from ansible_deployment import Deployment, cli_helpers, unlock_deployment, lock_deployment
from ansible_deployment.cli_autocomplete import (
    RoleType,
    HostType,
    InventoryWriterType,
    InventorySourceType,
    ShowAttributeType,
    GroupVarsType
)
from ansible_deployment.config import (
    DEFAULT_DEPLOYMENT_CONFIG_PATH,
    DEFAULT_OUTPUT_JSON_INDENT
)
from ansible_deployment.class_skeleton import CustomJSONEncoder


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
        deployment = Deployment.load(DEFAULT_DEPLOYMENT_CONFIG_PATH)
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
        deployment = Deployment.load(DEFAULT_DEPLOYMENT_CONFIG_PATH, read_sources=True)
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
@click.argument("attribute", required=False, nargs=-1, type=ShowAttributeType())
def show(ctx, attribute):
    """
    Show deployment information.

    Deployment information may be filtered by specifying attribute(s).
    """
    with unlock_deployment(ctx.obj["DEPLOYMENT"], 'r') as deployment:
        try:
            deployment.inventory.run_reader_plugins()
        except Exception as err:
            raise click.ClickException(err)
        output = deployment
        if attribute:
            try:
                output = cli_helpers.filter_output_by_attribute(output, attribute)
            except Exception as err:
                raise click.ClickException(err)
        output = json.dumps(output, indent=DEFAULT_OUTPUT_JSON_INDENT,
                              cls=CustomJSONEncoder)
        output = highlight(output, lexers.JsonLexer(),
                           formatters.Terminal256Formatter(style="default"))
        click.echo(output)


@cli.command()
@click.pass_context
@click.option(
    "-l", "--limit", help="Limit playbook execution.", type=HostType()
)
@click.option(
    "-e", "--extra-var", help="Set extra var for playbook execution.", multiple=True,
    type=GroupVarsType()
)
@click.option(
    "-d", "--disable-host-key-checking",
    help="Disable ssh host key checking.", is_flag=True
)
@click.argument("role", required=False, nargs=-1, type=RoleType())
def run(ctx, role, limit, extra_var, disable_host_key_checking):
    """
    Run deployment with ansible-playbook.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        with unlock_deployment(deployment, 'r') as unlocked_deployment:
            cli_helpers.check_environment(unlocked_deployment)
            unlocked_deployment.run(role, limit=limit, extra_vars=extra_var,
                                    disable_host_key_checking=disable_host_key_checking)
    except Exception as err:
        raise click.ClickException(err)


@cli.command()
@click.pass_context
@click.option(
    "-w", "--from-writer",
    help="""Only delete deployment from specified inventory writer.
            May be specified multiple times.""",
    multiple=True,
    type=InventoryWriterType()
)
@click.option(
    "--non-interactive", is_flag=True, help="Don't ask before deleting deployment."
)
def delete(ctx, from_writer, non_interactive):
    """
    Delete deployment.

    Deletes all created files and directories in deployment directory and also
    purges deployment data from configured inventory writers.

    If `--from-writer` is specified the deployment will only be deleted
    from the specified inventory writers. The deployment directory will
    NOT be deleted if this option is used.
    """
    try:
        deployment = ctx.obj["DEPLOYMENT"]
        if non_interactive:
            deployment.inventory.delete_from_writers(from_writer)
            if len(from_writer) == 0:
                deployment.deployment_dir.delete(full_delete=True)
        else:
            ctx.invoke(show)
            if click.confirm("Delete deployment?"):
                deployment.inventory.delete_from_writers(from_writer)
                if len(from_writer) == 0:
                    deployment.deployment_dir.delete(full_delete=True)
    except Exception as err:
        if ctx.obj['DEBUG']:
            raise
        else:
            raise click.ClickException(err)


@cli.command()
@click.pass_context
def lock(ctx):
    """
    Encrypt all deployment files except the roles directory.
    """
    try:
        deployment = Deployment.load(DEFAULT_DEPLOYMENT_CONFIG_PATH, read_sources=False)
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
        deployment = Deployment.load(DEFAULT_DEPLOYMENT_CONFIG_PATH)


@cli.command()
@click.pass_context
@click.argument("host", type=HostType())
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


@cli.command()
@click.option('--template-mode', is_flag=True,
              help='Run inventory writers without ssh and deployment keys.')
@click.option('--force', is_flag=True,
              help='Force push.')
@click.pass_context
def push(ctx, template_mode=False, force=False):
    """
    Run configured ìnventory_writers and push encrypted git repo.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    with lock_deployment(deployment) as locked_deployment:
        try:
            locked_deployment.deployment_dir.deployment_repo.push(force)
        except Exception as err:
            if ctx.obj["DEBUG"]:
                raise
            else:
                raise click.ClickException(err)

    deployment = Deployment(deployment.deployment_dir.path, deployment.config)
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
    "-s", "--from-source", help="""Only query given inventory sources.
                                   May be specified multiple times.""",
    multiple=True,
    type=InventorySourceType()
)
def update(ctx, non_interactive, from_source):
    """
    Update deployment.

    Updates deployment inventory from inventory_sources and pulls changes
    from roles repository.

    If `--from-source` is specified the roles repository will still be updated
    but only the given inventory sources will be queried for updates.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    with unlock_deployment(deployment) as unlocked_deployment:
        try:
            cli_helpers.update_deployment(unlocked_deployment, 'all', 
                non_interactive, sources_override=from_source)
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
@click.argument("inventory_source", type=InventorySourceType())
def fetch_key(ctx, inventory_source):
    """
    Fetch deployment key from given inventory source.
    """
    deployment = ctx.obj["DEPLOYMENT"]
    try:
        deployment.fetch_key(inventory_source)
    except Exception as err:
        if ctx.obj['DEBUG']:
            raise
        else:
            raise click.ClickException(err)

def main():
    """
    This function is only used to set 'auto_envvars_prefix'.
    """
    cli(auto_envvar_prefix="AD")


if __name__ == "__main__":
    main()
