# ansible-deployment

## Table Of Contents
- [ansible-deployment](#ansible-deployment)
  * [Overview](#overview)
  * [Requirements](#requirements)
  * [Quick Start](#quick-start)
    + [Setup](#setup)
    + [Configuration](#configuration)
      - [Example 1: Locally managed terraform deployment](#example-1--locally-managed-terraform-deployment)
      - [Example 2: Locally managed terraform deployment with local overwrite](#example-2--locally-managed-terraform-deployment-with-local-overwrite)
  * [Inventory Sources](#inventory-sources)
    + [local](#local)
    + [terraform](#terraform)
    + [vault](#vault)
  * [Inventory Writers](#inventory-writers)
    + [vault](#vault-1)

## Overview
ansible-deployment is a cli application for managing ansible deployments.

It will initialize a ready to use deployment directory from it's configuration
file ``deployment.json```. 

This file specifies which ansible roles the deployment will use in it's
playbook and from which git repository to get them from.

The configuration also specifies ``inventory_sources`` and ``ìnventory_writers``.

Deployment inventories can be sourced by multiple ``ìnventory_sources`` and
will be merged in the specified order and produce the final deployment inventory.

``ìnventory_writers`` persist the deployment inventory.

When initialized ansible-deployment will:
- clone the configured roles repository into deployment directory
- generate a playbook based on specified roles
- write role defaults as group_vars/ROLE_NAME
- apply inventory sources
    - if multiple inventory sources are used, they will be merged
    - the last specified inventory plugin will overwrite previously specified keys
- create a local git repository for the deployment directory

The idea of this tool is to enforce structure on ansible role development
and usage. All deployment roles' default variables will be written
as group_vars into the deployment inventory. So ideally ansible roles
used with ansible-deployment have all their variables that reflect
deployment specific configuration declared as such.

Each role will add an inventory group with the same name and will have 
a group called 'ansible-deployment' as their child and all parsed hosts
will be added to this 'ansible-deployment' group.

## Requirements
- python >= 3.9

## Quick Start
### Setup
ansible-deployment is shipped as a python package and can be installed via pip:

```
$ pip install .
```

### Configuration

#### Example 1: Locally managed terraform deployment
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
Values supplied by the terraform ``ìnventory_source`` will alway overwrite
the local deployment inventory. Inventory variables that are not supplied
by terraform still can be locally managed.

#### Example 2: Locally managed terraform deployment with local overwrite
```
$ cat deployment.json 
{
    "name": "locally managed terraform deployment with local overwrite",
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
        "terraform",
        "local"
    ],
    "inventory_writers": [
    ]
}
```

This configuration example will source it's inventory from a
``terraform.tfstate`` file inside the deployment directory and then apply
the local deployment inventory on top of it. This will allow the local
deployment inventory to overwrite any terraform supplied inventory values.

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
