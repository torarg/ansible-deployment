"""
Module containting the DeploymentRepo class.
"""

from pathlib import Path
import gitdb.exc as git_exc
from git import Repo
from git.exc import GitCommandError
from ansible_deployment.class_skeleton import AnsibleDeployment

class RepoOriginError(Exception):
    pass


class DeploymentRepo(AnsibleDeployment):
    """
    Represents a git repository used with ansible_deployment.

    Args:
        path (Path): Local path to git repository.
        remote_config (RepoConfig): Repository origin information.
        files (list): List of files included in repository.
        blobs (dict): Name (key) and Path (value) of object blobs.

    Attributes:
        path (Path): Local path to git repository.
        remote_config (RepoConfig): Repository origin information.
        content (list): List of files included in repository.
        changes (dict): Dictionary containing repository changes.
                        Valid keys are: 'all', 'staged' and 'unstaged'.
    """

    def __init__(self, path, remote_config=None, files=None, blobs={}):
        self.remote_config = remote_config
        self.path = path

        self.content = files
        self.blobs = blobs
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
            self.changes["staged"] = ["deployment.json"]
        self.changes["all"] = self.changes["staged"] + self.changes["unstaged"]

    def _cleanup_blobs(self):
        current_tags = self.repo.git.tag().split("\n")
        for blob_name in self.blobs:
            if blob_name in current_tags:
                self.repo.git.tag('-d', blob_name)
        self.repo.git.gc()
        self.repo.git.prune()

    def _store_blobs(self):
        for blob_name in self.blobs:
            blob_path = self.blobs[blob_name]
            blob_hash = self.repo.git.hash_object('-w', blob_path)
            message = "ansible-deployment blob object"
            self.repo.git.tag(blob_hash, a=blob_name, m=message)

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
                try:
                    self.repo.index.remove(str(git_file))
                except GitCommandError as e:
                    print(e)

        self.update_changed_files()
        commit_message = "ansible-deployment: {}".format(message.capitalize())
        if len(self.changes["staged"]) > 0 or force_commit:
            self.repo.index.commit(commit_message)

        self._cleanup_blobs()
        self._store_blobs()

    def _pull_blobs(self):
        for blob_name in self.blobs:
            blob_path = self.blobs[blob_name]
            blob_data = self.repo.git.show(blob_name).split("\n")[5]
            with open(blob_path, "w") as blob_file:
                blob_file.write(blob_data)

    def pull(self, blobs={}):
        """
        Pull changes from origin.
        """
        if 'origin' not in self.repo.remotes:
            raise RepoOriginError("Missing git remote origin")
        self.blobs = blobs
        self.repo.remotes.origin.fetch()
        if self.remote_config is not None:
            self.repo.git.checkout(self.remote_config.branch)
        if not self.repo.head.is_detached:
            self.repo.remotes.origin.pull()
            self._pull_blobs()

    def push(self):
        """
        Push changes to origin.
        """
        if 'origin' not in self.repo.remotes:
            raise RepoOriginError("Missing git remote origin")
        self.repo.remotes.origin.fetch()
        if self.remote_config is not None:
            self.repo.git.checkout(self.remote_config.branch)
        if not self.repo.head.is_detached:
            self.repo.remotes.origin.push()
            if self.blobs:
                self.repo.git.push("-f", "--tags")

    def clone(self):
        """
        Clone remote reopository.

        Clones the repository specified in `self.remote_config` into
        `self.path`
        """
        self.repo = Repo.clone_from(
            self.remote_config.repo, self.path, branch=self.remote_config.branch
        )

    def write_changelog(self):
        changelog_path = self.path / "CHANGELOG"
        deployment_commits = self.repo.git.log("--pretty=format:'%H'")
        with open(changelog_path, "w") as f:
            f.write(deployment_commits)

    def init(self):
        """
        Initialize empty repository.
        """
        self.repo = Repo.init(self.path)
