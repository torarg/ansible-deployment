# 0.8.0 (upcoming)
- generate ssh key during deployment initialization
- replace '-' with '_' in group names derived from role names
- improve error handling

# 0.7.0 (2021/03/31)
- improve documentation
- add roles/ directory to deployment repo
- upstream roles repo is now stored in .roles.git inside deployment directory

# 0.6.0 (2021/03/07)
- add ``ansible_user`` to ``group_vars`` by default
- add fetch and checkout of roles during update. this enables branch or tag changing
- add persist command to run ``inventory_writers``
- no longer run ``inventory_writers`` on update and init commands
- fix handling of added files from inventory plugins
- add ``deployment.key`` to deployment repo and inventory

# 0.5.1 (2021/03/05)
- fix package requirements

# 0.5.0 (2021/03/05)
- move to semantic versioning
- add local inventory source plugin
- add vault inventory source plugin
- add vault inventory writer plugin
- split up inventory plugins into inventory_sources and inventory_writers
- change inventory file structure to explicitly list all hosts in groups
- fix inventory update to add new vars files to deployment repo
- clear screen before showing diff during update
- display newly added files during update

# 0.4 (2021/02/03)
- Fixed a bug in inventory creation from terraform state files containing multiple instances of resources
