# ansible-deployment

## overview
ansible-deployment is a cli application for managing ansible deployments.

Deployments can either be stateless or stateful depending on the configured
``inventory_sources`` and ``inventory_writers``.

When initialized ansible-deployment will:

    - clone the configured roles repository into deployment directory
    - generate a playbook based on specified roles
    - write role defaults as group_vars/ROLE_NAME
    - apply inventory sources
        - if multiple inventory sources are used, they will be merged
        - the last specified inventory plugin will overwrite previously specified keys
    - write the final deployment inventory to all ``inventory_writers``
    - create a local git repository for the deployment directory

The idea of this tool is to enforce structure on ansible role development
and usage. All deployment roles' default variables will be written
as group_vars into the deployment inventory. So ideally ansible roles
used with ansible-deployment have all their variables that reflect
deployment specific configuration declared as such.

Each role will add an inventory group with the same name and will have 
a group called 'ansible-deployment' as their child and all parsed hosts
will be added to this 'ansible-deployment' group.

In addition to this role defaults based inventory creation one ore more 
inventory sources may be specified to update the inventory.


## inventory sources
Inventory sources specify where from and in which order the deployment
inventory is created.

If multiple inventory sources are specified the deployment inventory will
be merged from all specified sources in the specified order. Meaning the last
inventory source will always take precedence if the same key is gathered
from multiple inventory sources.

Currently ansible deployment supports the following ``inventory_sources``.


### local
The ``local`` inventory source is always the first inventory source and 
is not required to be explicizly specified in ``deployment.json```.

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
    - VAULT_ADDR
    - VAULT_TOKEN

All hosts, host_vars and group vars specified in the path
``secret/ansible-deployment/DEPLOYMENT_NAME`` will be added to the inventory

Currently only kv is supported as secrets engine. It's path is expected to be 
in 'secret/' 


## inventory writers
Inventory writers persist the state of the deployment inventory and will be 
executed after updates and deployment initialization.

Currently ansible deployment supports the following ``inventory_writers``.


### vault
The ``vault`` inventory writer requires a configured vault environment
consisting of the following environment variables:
    - VAULT_ADDR
    - VAULT_TOKEN

The current deployment inventory will be written in the vault path
``secret/ansible-deployment/DEPLOYMENT_NAME``.

Currently only kv is supported as secrets engine. It's path is expected to be 
in 'secret/' 


## setup

```
pip install .
```

## configuration

ansible-deployment requires a deployment.json configuration file
to be present in the current working directory.

### example


## stateful deployment with dynamic terraform inventory
This example sources it's inventory first from terraform and then applies
locally commited changes on top of it. The resulting inventory is persisted
in vault.

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
    "inventory_sources": [
        "terraform",
        "local"
    ],
    "inventory_writers": [
        "vault"
    ],

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

## stateless vault inventory
This example sources it's inventory completely from vault.

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
    "inventory_sources": [
        "vault"
    ],
    "inventory_writers": [
    ],

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
