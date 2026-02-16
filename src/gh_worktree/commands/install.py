import os
import shutil
import stat
import sys
from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple

from gh_worktree.command import Command


class InstallCommand(Command):
    _name = "install"

    def __call__(
        self,
        alias: Optional[str] = None,
        gh_ext: bool = False,
        path_bin: bool = False,
        force: bool = False,
    ):
        """Installs gh-worktree as a GitHub CLI extension or to the user's PATH.

        Without specifying options, the install command will ask you what to do.

        :param alias: An alternate name for the extension or path command.
        :param gh_ext: Install as a GitHub CLI extension.
        :param path_bin: Install to the user's PATH.
        :param force: Overwrite existing files.
        """
        target_name = alias or "gh-worktree"
        gh_ext, path_bin = self._ask(target_name, gh_ext, path_bin)

        current_script_path = Path(sys.argv[0]).resolve()
        should_link = False

        # unless the script is a self-contained executable, link it instead of copy
        if current_script_path.suffix == ".py":
            should_link = True
        elif not current_script_path.suffix and str(current_script_path).endswith(
            ".venv/bin/gh-worktree"
        ):
            should_link = True

        target_paths = []

        if gh_ext:
            ext_name = target_name
            if not ext_name.startswith("gh-"):
                ext_name = f"gh-{target_name}"
            target_paths.append(
                Path("~/").expanduser()
                / ".local"
                / "share"
                / "gh"
                / "extensions"
                / ext_name
                / ext_name
            )

        if path_bin:
            target_path = Path("~/").expanduser() / ".local"
            while str(target_path / "bin") not in os.getenv("PATH", ""):
                if target_path == target_path.parent:
                    print("Could not find suitable directory in path")
                    return
                target_path = target_path.parent
            target_paths.append(target_path / "bin" / target_name)

        self._run(current_script_path, target_paths, should_link, force)

    def _run(
        self,
        current_script_path: Path,
        target_paths: List[Path],
        should_link: bool,
        force: bool,
    ):
        for target_path in target_paths:
            if target_path.exists() and not force:
                print(f"Path already exists, use --force to overwrite: {target_path}")
                sys.exit(1)

            target_path.parent.mkdir(parents=True, exist_ok=True)

            if should_link:
                os.link(current_script_path, target_path)
            else:
                shutil.copy(current_script_path, target_path)
                target_path.chmod(target_path.stat().st_mode | stat.S_IEXEC)
            print(f"Installed to {target_path}")

    def _ask(self, target_name: str, gh_ext: bool, path_bin: bool) -> Tuple[bool, bool]:
        # ask user what path they would like to use for installation, without these args
        if not gh_ext and not path_bin:
            print("Tip: Re-run this with --alias to change the name\n")
            print("Which method do you want to use?")
            print(
                f"\t1. As a GitHub CLI (gh) extension: gh {target_name.replace('gh-', '')}"
            )
            print(f"\t2. In your PATH: {target_name}\n")

            choice = input("Your choice (1, 2): ")
            if choice not in ("1", "2"):
                print("Invalid choice")
                sys.exit(1)

            if choice == "1":
                gh_ext = True
            elif choice == "2":
                path_bin = True
        return gh_ext, path_bin
