# ansible-deployment

## overview

ansible-deployment is a cli application for generating deployment
directories from an inventory plugin and a set of roles.

The deployment directory includes:

- a hosts.yml file containing all hosts and a group for every imported role
- a group_vars directory containing all role defaults as group vars
- a host_vars directory containing inventory plugin variables
- a playbook template which imports and tags used roles
- a git repository tracking the state of the deployment

Currently the only supported inventory plugin is 'terraform' and so far
it only supports the use of 'hcloud' resources since managing those
was my primary use case while writing this application.

## setup

```
pip install .
```

## usage

```
Usage: ansible-deployment [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  delete  Delete deployment.
  init    Initialize deployment directory.
  lock    Encrypt all deployment files except the roles directory.
  run     Run deployment with ansible-playbook.
  show    Show deployment information.
  ssh     Run 'ssh' command to connect to a inventory host.
  unlock  Decrypt all deployment files except the roles directory.
  update  Updates all deployment files and directories.
```

For further information: https://www.1wilson.org/restricted/docs/cli.html#ansible-deployment
