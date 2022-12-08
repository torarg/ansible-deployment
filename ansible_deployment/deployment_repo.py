"""
Module containting the DeploymentRepo class.
"""

from pathlib import Path
import gitdb.exc as git_exc
from git import Repo
from ansible_deployment.class_skeleton import AnsibleDeployment


class DeploymentRepo(AnsibleDeployment):
    """
    Represents a git repository used with ansible_deployment.

    Args:
        path (Path): Local path to git repository.
        remote_config (RepoConfig): Repository origin information.
        files (list): List of files included in repository.

    Attributes:
        path (Path): Local path to git repository.
        remote_config (RepoConfig): Repository origin information.
        content (list): List of files included in repository.
        changes (dict): Dictionary containing repository changes.
                        Valid keys are: 'all', 'staged' and 'unstaged'.
    """

    def __init__(self, path, remote_config=None, files=None):
        self.remote_config = remote_config
        self.path = path

        self.content = files
        self.changes = {"all": [], "staged": [], "unstaged": [], "new": []}
        self._git_path = self.path / ".git"
        self._encrypted = (self._git_path / "HEAD.enc").exists()

        if (self._git_path / "HEAD").exists() and not self._encrypted:
            self.repo = Repo(self.path)
            self.update_changed_files()
        else:
            self.repo = None

    def update_changed_files(self):
        """
        Update `self.changes` dict to represent state of git repo.
        """
        for untracked_file in self.repo.untracked_files:
            if untracked_file in self.changes["new"]:
                continue
            if "host_vars/" in untracked_file:
                self.changes["new"].append(untracked_file)
            elif "group_vars/" in untracked_file:
                self.changes["new"].append(untracked_file)
            elif "roles/" in untracked_file:
                self.changes["new"].append(untracked_file)
            elif self.content is not None and untracked_file in self.content:
                self.changes["new"].append(untracked_file)

        self.changes["unstaged"] = [diff.a_path for diff in self.repo.index.diff(None)]
        try:
            self.changes["staged"] = [
                diff.a_path for diff in self.repo.index.diff("HEAD")
            ]
        except git_exc.BadName:
            self.changes["staged"] = []
        self.changes["all"] = self.changes["staged"] + self.changes["unstaged"]

    def update(
        self,
        message="Automatic ansible-deployment update.",
        files=None,
        force_commit=False,
    ):
        """
        Updates the git repository.

        Args:
            message (str): Commit message.
            files (sequence): Files to commit.
            force_commit (bool): Whether or not to force an empty commit.

        The update will add the specified files and commit them.
        """
        if files is None:
            files = self.content
        for git_file in files:
            if Path(git_file).exists():
                self.repo.index.add(str(git_file))
            else:
                self.repo.index.remove(str(git_file))
        self.update_changed_files()
        if len(self.changes["staged"]) > 0 or force_commit:
            self.repo.index.commit(
                "ansible-deployment: {}".format(message.capitalize())
            )

    def pull(self):
        """
        Pull changes from origin.
        """
        self.repo.remotes.origin.fetch()
        self.repo.git.checkout(self.remote_config.branch)
        if not self.repo.head.is_detached:
            self.repo.remotes.origin.pull()

    def clone(self):
        """
        Clone remote reopository.

        Clones the repository specified in `self.remote_config` into
        `self.path`
        """
        self.repo = Repo.clone_from(
            self.remote_config.repo, self.path, branch=self.remote_config.branch
        )

    def init(self):
        """
        Initialize empty repository.
        """
        self.repo = Repo.init(self.path)
