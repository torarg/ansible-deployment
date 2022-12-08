# ansible-deployment

## Description
ansible-deployment is a cli application for creating, managing and updating
deployment repositories which are seperated from your actual role development repositories.

While having the management of roles in common with ansible-galaxy, ansible-deployment
also aims to assist your workflow over the whole deployment's lifecycle by
supporting plugins called ``inventory_sources`` and ``inventory_writers`` to 
source and persist the deployment inventory from and to different endpoints.


## Features
- creates a ready to use ansible deployment directory from a json definition.
- fetch and update roles from a remote git repository
- generate local inventory from role defaults and inventory plugins
  - source inventory from one or more sources with ``inventory_sources`` 
  - write inventory to one or more destinations with ``inventory_writers``
- encryption support


## Setup
### Requirements
The following software is not part of the python package requirements 
and needs to be installed manually:
- python >= 3.9
- ansible
- git



### Install as python package
ansible-deployment is shipped as a python package and can be installed via pip:

```
$ pip install ansible-deployment
```

## Quick Start


### Creating a deployment.json file
ansible-deployment needs at least a ``deployment.json`` file to initialize
a deployment directory:

```
$ mkdir -p ~/deployments/my_deployment
$ cat <<EOF > deployment.json
{
    "name": "my_deployment",
    "roles": [
        "openbsd_install_from_rescue",
        "sysupgrade",
        "bootstrap",
        "backup",
        "wireguard",
        "webserver",
        "gitea",
        "firewall",
        "add_to_icinga2"
    ],
    "roles_src": {
        "repo": "_gitea@git.1wilson.org:mw/ansible-roles.git",
        "branch": "master"
    },
    "inventory_sources": [
        "vault",
        "terraform"
    ],
    "inventory_writers": [
        "vault"
    ]
}
```

Theoretically we could already initialize our deployment at this point, but 
since we defined ``vault`` and ``terraform`` as ``inventory_sources`` we will
need to make sure those are ready to use.

### Configure inventory plugins

#### vault
The vault inventory source is configured via the same environment variables as the
vault cli client:
```
$ export VAULT_ADDR=https://vault.1wilson.home:8200
$ export VAULT_TOKEN=someToken
```

### terraform
Currently the terraform inventory source only supports Hetzner Cloud resources,
so we need a terraform state containing such resources to use it as our
inventory source. 
The state file is expected to reside in ``DEPLOYMENT_DIR/terraform.tfstate``


### Initialize deployment
Right now our deployment directory should at least contain the following files:

```
$ ls
deployment.json  terraform.tfstate
```

To initalize the deployment directory we use ansible-deployment's ``init`` command:

```
$ ansible-deployment init
Deployment key written to: /home/mw/Deployments/my_deployment/deployment.key
{   'deployment_dir': {   'path': '/home/mw/Deployments/my_deployment',
                          'roles_src': "RepoConfig(repo='_gitea@git.1wilson.org:mw/ansible-roles.git', "
                                       "branch='master')"},
    'inventory': {},
    'name': 'my_deployment',
    'roles': [   'openbsd_install_from_rescue',
                 'sysupgrade',
                 'bootstrap',
                 'backup',
                 'wireguard',
                 'webserver',
                 'gitea',
                 'firewall',
                 'add_to_icinga2']}
(Re)Initialize Deployment? [y/N]: y
```

Now we have a ready to use deployment directory sourced from terraform.

```
[mw@mw-arch my_deployment]$ ls -la
insgesamt 28
drwxr-xr-x 1 mw mw  240 19. Jan 23:47 .
drwxr-xr-x 1 mw mw  210 19. Jan 23:43 ..
-rw-r--r-- 1 mw mw   91 19. Jan 23:47 ansible.cfg
-rw-r--r-- 1 mw mw 1952 19. Jan 23:44 deployment.json
-rw------- 1 mw mw   44 19. Jan 23:47 deployment.key
drwxr-xr-x 1 mw mw  138 19. Jan 23:47 .git
drwxr-xr-x 1 mw mw  200 19. Jan 23:47 group_vars
-rw-r--r-- 1 mw mw  725 19. Jan 23:47 hosts.yml
drwxr-xr-x 1 mw mw   18 19. Jan 23:47 host_vars
-rw-r--r-- 1 mw mw 2643 19. Jan 23:47 playbook.yml
drwxr-xr-x 1 mw mw  194 19. Jan 23:47 roles
drwxr-xr-x 1 mw mw  596 19. Jan 23:47 .roles.git
drwxr-xr-x 1 mw mw   32 19. Jan 23:47 .ssh
-rw-r--r-- 1 mw mw 7000 19. Jan 23:44 terraform.tfstate
```

### Usage
```
$ ansible-deployment --help
Usage: ansible-deployment [OPTIONS] COMMAND [ARGS]...

  All available commands are listed below.

  Each command has it's own help that can be shown by passing '--help':

      $ ansible-deployment COMMAND --help

Options:
  --version  Show the version and exit.
  --debug    Enable debug output.
  --help     Show this message and exit.

Commands:
  commit  Commit all changes.
  delete  Delete deployment.
  edit    Edit deployment.
  init    Initialize deployment directory.
  lock    Encrypt all deployment files except the roles directory.
  pull    Pull encrypted git repo.
  push    Run configured ìnventory_writers and push encrypted git repo.
  run     Run deployment with ansible-playbook.
  show    Show deployment information.
  ssh     Run 'ssh' command to connect to a inventory host.
  unlock  Decrypt all deployment files except the roles directory.
  update  Updates all deployment files and directories.
```
