import gitdb.exc as git_exc
from collections import namedtuple
from pathlib import Path
from git import Repo


class DeploymentRepo:
    def __init__(self, path, remote_config=None, files=[]):
        self.remote_config = remote_config
        self.path = path

        self.content = files
        self.changes = {'all': [],'staged': [], 'unstaged': []}
        self._git_path = self.path / '.git'
        self._encrypted = (self._git_path / 'HEAD.enc').exists()

        if self._git_path.exists() and not self._encrypted:
            self.repo = Repo(self.path)
            self.update_changed_files()
        else:
            self.repo = None


    def update_changed_files(self):
        """
        Update `self.changes` dict to represent state of git repo.
        """
        if not self.repo:
            return None
        self.changes['unstaged'] = [
            diff.a_path for diff in self.repo.index.diff(None)
        ]
        try:
            self.changes['staged'] = [
                diff.a_path for diff in self.repo.index.diff('HEAD')
            ]
        except git_exc.BadName:
            self.changes['staged'] = []
        self.changes['all'] = self.changes['staged'] + self.changes['unstaged']

    def update(self,
               message="Automatic ansible-deployment update.",
               files=None,
               force_commit=False):
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
                self.repo.index.add(git_file)
        self.update_changed_files()
        if len(self.changes['staged']) > 0 or force_commit:
            self.repo.index.commit("ansible-deployment: {}".format(
                message.capitalize()))

    def pull(self):
        self.repo.remotes.origin.pull()

    def clone(self):
        self.repo = Repo.clone_from(self.remote_config.repo, self.path,
                                    branch=self.remote_config.branch)

    def init(self):
        self.repo = Repo.init(self.path)
