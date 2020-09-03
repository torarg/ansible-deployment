import click


def err_exit(error_message):
    """
    Exit with click.context.fail() method.

    Args:
        error_message (str): Message to print on exit.
    """
    cli_context = click.get_current_context()
    cli_context.fail(error_message)


def filter_output_by_attribute(output, attribute):
    """
    Filter output dict by a sequence of nested lookup keys.

    Args:
        output (dict): dict to filter.
        attribute (iter): sequence of nested lookup keys.

    Returns:
        dict: a dict only containing the nested attribute lookup.
    """
    for attr in attribute:
        if attr not in output:
            err_exit('Attribute not found')
        output = output[attr]
    return output


def check_environment(deployment):
    """
    Check if deployment object is ready for further cli processing.

    Args:
        deployment (Deployment): deployment object to check

    If checking fails the program will be terminated by err_exit()
    """
    if not deployment:
        err_exit("Failed to load deployment.json")
    elif deployment.deployment_dir.repo.is_dirty():
        err_exit("Repo is dirty. Unstaged changes: {}".format(
            deployment.deployment_dir.unstaged_changes))
    elif not deployment.deployment_dir.roles_path.exists():
        err_exit("Deployment directory not initialized.")


def echo_file_diff(deployment_dir, file_name):
    """
    Echo a git diff for a given file.

    Args:
        deployment_dir (DeploymentDirectory): Deployment directory.
        file_name (str): File name to display diff for.
    """
    if file_name in deployment_dir.unstaged_changes:
        click.echo(deployment_dir.repo.git.diff(file_name))
    elif file_name in deployment_dir.staged_changes:
        click.echo(deployment_dir.repo.git.diff('--staged', file_name))


def prompt_for_update_choices(deployment_dir):
    """
    Prints diffs for changed files to STDOUT and asks for a update strategy.

    Args:
        deployment_dir (DeploymentDirectory): deployment directory object.

    Returns:
        list: List of file names with update strategy 'apply'.
    """
    files_to_commit = []
    prompt_message = 'Please select update strategy ([a]pply, [d]iscard, [k]eep unstaged)'
    prompt_choice = click.Choice(('a', 'd', 'k'))
    prompt_actions = {
        'a': files_to_commit.append,
        'd': deployment_dir.repo.git.checkout
    }
    for file_name in deployment_dir.changes:
        echo_file_diff(deployment_dir, file_name)
        update_choice = click.prompt(prompt_message,
                                     default='k',
                                     type=prompt_choice,
                                     show_choices=False)
        if update_choice in prompt_actions:
            prompt_actions[update_choice](file_name)

    return files_to_commit