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
ansible-deployment [OPTIONS] COMMAND [ARGS]...
```

### Options


### --version
Show the version and exit.

### delete

Delete deployment.

Deletes all created files and directories in deployment directory.

```
ansible-deployment delete [OPTIONS]
```

### init

Initialize deployment directory.

Initialization requires a ‘deployment.json’ file in the
current working directory.

```
ansible-deployment init [OPTIONS]
```

### run

Run deployment with ansible-playbook.

This will create a commit in the deployment repository
containing the executed command.

```
ansible-deployment run [OPTIONS] [ROLE]...
```

### Arguments


### ROLE
Optional argument(s)

### show

Show deployment information.

Deployment information may be filtered by specifying attribute(s).

```
ansible-deployment show [OPTIONS] [ATTRIBUTE]...
```

### Arguments


### ATTRIBUTE
Optional argument(s)

### ssh

Run ‘ssh’ command to connect to a inventory host.

```
ansible-deployment ssh [OPTIONS] HOST
```

### Arguments


### HOST
Required argument

### update

Updates all deployment files and directories.

This will pull new changes from the roles source repository and
update all deployment files accordingly.
All changes will be shown as diff and the user needs to decide a.
update strategy.

```
ansible-deployment update [OPTIONS]
```
