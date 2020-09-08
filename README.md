# ansible-deployment

## overview

ansible-deployment is a cli application managing ansible deployments.

It features:

- generating a deployment directory from:
    - an ansible roles git repository
    - an inventory plugin
    - a config file defining roles and inventory plugin
- the deployment directory will include 

    playbook.yml: a templated playbook including specified roles
    group_vars/*: containing each role's defaults seperated by group
    host_vars/* : containing inventory plugin information
    hosts.yml   : inventory file with host and group assignments
    .git        : a git repository tracking changes the deployment

The idea of this tool is to enforce structure on ansible role development
and usage. All deployment roles' default variables will be written
as group_vars into the deployment inventory. So ideally ansible roles
used with ansible-deployment have all their variables that reflect
deployment specific configuration declared as such.

Each role will add an inventory group with the same name and will have 
a group called 'ansible-deployment' as their child and all parsed hosts
will be added to this 'ansible-deployment' group.

Currently the only supported inventory plugin is 'terraform' and so far
it only supports the use of 'hcloud' resources since managing those
was my primary use case while writing this application.

## setup

```
pip install .
```

## configuration

ansible-deployment requires a deployment.json configuration file
to be present in the current working directory.

### example
```
$ cd mydeployment/
$ ls -l
-rw-r--r--  1 mw  staff   408  6 Sep 23:28 deployment.json
-rw-r--r--  1 mw  staff  3472  6 Sep 23:29 terraform.tfstate
$ cat deployment.json
{
    "roles": [
        "openbsd_install_from_rescue",
        "bootstrap",
        "wireguard",
        "dns_server",
        "webserver",
        "mailserver",
        "gitea",
        "firewall",
        "data_sync"
    ],
    "roles_src": {
        "repo": "git@github.com:torarg/ansible-roles.git",
        "branch": "master"
    },
    "inventory_plugin": "terraform",
    "ansible_user": "ansible"
}
$ ansible-deployment init
$ ls -l
-rw-r--r--   1 mw  staff    58  7 Sep 00:27 ansible.cfg
-rw-r--r--   1 mw  staff   408  6 Sep 23:28 deployment.json
-r--------   1 mw  staff    44  7 Sep 00:27 deployment.key
drwxr-xr-x  11 mw  staff   352  7 Sep 00:27 group_vars
drwxr-xr-x   3 mw  staff    96  7 Sep 00:27 host_vars
-rw-r--r--   1 mw  staff   686  7 Sep 00:27 hosts.yml
-rw-r--r--   1 mw  staff  2544  7 Sep 00:27 playbook.yml
drwxr-xr-x  22 mw  staff   704  7 Sep 00:27 roles
-rw-r--r--   1 mw  staff  3472  6 Sep 23:29 terraform.tfstate
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
