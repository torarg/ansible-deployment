# ansible-deployment

- [Description](#description)
- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
  * [Setup](#setup)
  * [Configuration](#configuration)
    + [Example: Terraform inventory](#example--terraform-inventory)
- [Inventory Sources](#inventory-sources)
  * [local](#local)
  * [terraform](#terraform)
  * [vault](#vault)
- [Inventory Writers](#inventory-writers)
  * [vault](#vault-1)


## Description
ansible-deployment is a cli application for managing ansible deployments in
an effective matter.

## Features
- creates a ready to use ansible deployment directory
- roles fetched via git
- git managed
- inventory queried and merged from ``ìnventory_sources``
- save command for persistation through ``inventory_writers``
- update command to query for role or inventory changes


## Requirements
- python >= 3.9

## Quick Start
### Setup
ansible-deployment is shipped as a python package and can be installed via pip:

```
$ pip install .
```

### Configuration

#### Example: Terraform inventory
```
$ cat deployment.json 
{
    "name": "locally managed terraform deployment",
    "roles": [
        "bootstrap",
        "webserver",
        "gitea"
    ],
    "roles_src": {
        "repo": "git@github.com:torarg/ansible-roles.git",
        "branch": "master"
    },
    "inventory_sources": [
        "terraform"
    ],
    "inventory_writers": [
    ]
}
```

This configuration example will source it's inventory from a
``terraform.tfstate`` file inside the deployment directory.
Values supplied by the terraform ``ìnventory_source`` will always overwrite
the local deployment inventory. Inventory variables that are not supplied
by terraform still can be locally managed.

```
$ ls
deployment.json         servers.tf              terraform.tfstate       versions.tf

$ ansible-deployment init
Deployment key written to: /Users/mw/Deployments/example/deployment.key
{   'deployment_dir': {   'path': '/Users/mw/Deployments/example',
                          'roles_src': "RepoConfig(repo='git@github.com:torarg/ansible-roles.git', "
                                       "branch='master')"},
    'inventory': {   'dev': {'ansible_host': 'XXX.XXX.XXX.XXX'},
                     'www': {'ansible_host': 'XXX.XXX.XXX.XXX'}},
    'name': 'locally managed terraform deployment',
    'roles': ['bootstrap', 'webserver', 'gitea']}
(Re)Initialize Deployment? [y/N]: y
michaelwilson@mw-mac openbsd-disk-encryption-test % ls -l
total 72
-rw-r--r--   1 michaelwilson  staff    91  9 Mär 00:18 ansible.cfg
-rw-r--r--   1 michaelwilson  staff   352  8 Mär 23:33 deployment.json
-rw-------   1 michaelwilson  staff    44  9 Mär 00:18 deployment.key
drwxr-xr-x   6 michaelwilson  staff   192  9 Mär 00:18 group_vars
drwxr-xr-x   4 michaelwilson  staff   128  9 Mär 00:18 host_vars
-rw-r--r--   1 michaelwilson  staff   183  9 Mär 00:18 hosts.yml
-rw-r--r--   1 michaelwilson  staff  1616  9 Mär 00:18 playbook.yml
drwxr-xr-x  26 michaelwilson  staff   832  9 Mär 00:18 roles
-rw-r--r--   1 michaelwilson  staff   790  3 Feb 11:39 servers.tf
-rw-r--r--   1 michaelwilson  staff  7338  7 Mär 23:36 terraform.tfstate
-rw-r--r--   1 michaelwilson  staff   130 31 Jan 11:06 versions.tf
```

## Inventory Sources
Inventory sources specify where from and in which order the deployment
inventory is created.

If multiple inventory sources are specified the deployment inventory will
be merged from all specified sources in the specified order. Meaning the last
inventory source will always take precedence if the same key is gathered
from multiple inventory sources.

Currently ansible deployment supports the following ``inventory_sources``.


### local
The ``local`` inventory source is always the first inventory source and 
is not required to be explicitly specified in ``deployment.json``.

However if you wish to overwrite values supplied by another inventory source,
you may specify ``local`` as inventory source.

For example if you would like to query the deployment inventory from vault
but would like to overwrite the supplied values locally:
```
$ cat deployment.json
[...]
    "inventory_sources": [
        "vault",
        "local"
    ],
[...]
```


### terraform
The ``terraform`` inventory source requires a ``terraform.tfstate`` file
present in the deployment directory. It will read all hosts from the
terraform state and add them to the inventory as well to each deployment
group.

Currently only 'hcloud' resources are supported.


### vault
The ``vault`` inventory source requires a configured vault environment
consisting of the following environment variables:
- ``VAULT_ADDR``
- ``VAULT_TOKEN``

All hosts, host_vars and group vars specified in the path
``secret/ansible-deployment/DEPLOYMENT_NAME`` will be added to the inventory

Currently only kv is supported as secrets engine. It's path is expected to be 
in 'secret/' 


## Inventory Writers
Inventory writers persist the state of the deployment inventory and will be 
executed when the ``persist`` subcommand is executed.

Currently ansible deployment supports the following ``inventory_writers``.


### vault
The ``vault`` inventory writer requires a configured vault environment
consisting of the following environment variables:
- ``VAULT_ADDR``
- ``VAULT_TOKEN``

The current deployment inventory will be written in the vault path
``secret/ansible-deployment/DEPLOYMENT_NAME``.

Currently only kv is supported as secrets engine. It's path is expected to be 
in 'secret/' 
