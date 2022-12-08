# ansible-deployment

## description
ansible-deployment is a cli utility to manage role based ansible deployments.

## pip installation
pip3 install .

## define a deployment
add a deployment.json file to your deployment directory.

example:
```
$ cat ./deployment.json
{
    "name": "mw-hcloud",
    "roles": [
        "00_openbsd_install_from_rescue",
        "01_bootstrap",
        "03_webserver"
    ],
    "inventory_type": "terraform",
    "ansible_roles_src": {
        "repo": "git@github.com:torarg/ansible-roles.git",
        "branch": "master"
    }
}
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
  run     Run deployment with ansible-playbook.
  show    Show deployment information.
  ssh     SSH into a given host of deployment inventory.
  update  Update deployment roles.
```
