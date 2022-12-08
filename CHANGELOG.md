# CHANGELOG
## 1.0.0 (upcoming)
- add `update-known-hosts` command
- add option to override inventory sources during update
- add `fetch-key` command
- fix group_vars not updating when new role defaults were defined
- fix several bugs in deployment push&pull
## 0.9.0 (2022/07/08)
- inventory writers now support deletion of written data
- fix usage of roles inside of sub directories
- add update command again
- add reset command
- add diff command
- fix host lookup for ssh subcommand if host has host_vars defined

## 0.8.0 (2022/01/22)
- improve delete workflow
- add shasum verification for encrypted deployment
- support commands on locked deployment
- support storage of encrypted deployment as git object
- add push command
- add pull command
- add edit command
- add commit command
- improve deployment encryption
- fix deprecated usage of collections
- multistage docker build
- add custom ca support for vault plugins
- add template functionality for inventory writers
- add ssh key support for vault plugins
- improve variable merging
- generate ssh key during deployment initialization
- replace '-' with '_' in group names derived from role names
- improve error handling

## 0.7.0 (2021/03/31)
- improve documentation
- add roles/ directory to deployment repo
- upstream roles repo is now stored in .roles.git inside deployment directory

## 0.6.0 (2021/03/07)
- add ``ansible_user`` to ``group_vars`` by default
- add fetch and checkout of roles during update. this enables branch or tag changing
- add persist command to run ``inventory_writers``
- no longer run ``inventory_writers`` on update and init commands
- fix handling of added files from inventory plugins
- add ``deployment.key`` to deployment repo and inventory

## 0.5.1 (2021/03/05)
- fix package requirements

## 0.5.0 (2021/03/05)
- move to semantic versioning
- add local inventory source plugin
- add vault inventory source plugin
- add vault inventory writer plugin
- split up inventory plugins into inventory_sources and inventory_writers
- change inventory file structure to explicitly list all hosts in groups
- fix inventory update to add new vars files to deployment repo
- clear screen before showing diff during update
- display newly added files during update

## 0.4 (2021/02/03)
- Fixed a bug in inventory creation from terraform state files containing multiple instances of resources
