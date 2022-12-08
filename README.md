# ansible_deployment.cli

## ansible-deployment

```
ansible-deployment [OPTIONS] COMMAND [ARGS]...
```

### Options


### --version()
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


### ROLE()
Optional argument(s)

### show

Show deployment information.

Deployment information may be filtered by specifying attribute(s).

```
ansible-deployment show [OPTIONS] [ATTRIBUTE]...
```

### Arguments


### ATTRIBUTE()
Optional argument(s)

### ssh

Run ‘ssh’ command to connect to a inventory host.

```
ansible-deployment ssh [OPTIONS] HOST
```

### Arguments


### HOST()
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
