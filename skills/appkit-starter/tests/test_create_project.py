from __future__ import annotations

import importlib.util
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "create_project.py"
TEMPLATE_ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("create_project", SCRIPT_PATH)
create_project = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(create_project)


def copy_template(destination: Path) -> None:
    shutil.copytree(
        TEMPLATE_ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", ".DerivedData", "__pycache__"),
    )


def text_files(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        paths.append(path)
    return paths


class InputValidationTests(unittest.TestCase):
    def test_defaults_are_deterministic(self) -> None:
        self.assertEqual(
            create_project.resolve_display_name("ShelfMac", None),
            "ShelfMac",
        )
        self.assertEqual(
            create_project.resolve_bundle_id("ShelfMac", "owner/ShelfMac", None),
            "com.example.shelfmac",
        )

    def test_rejects_unsafe_repository_and_bundle_identifiers(self) -> None:
        with self.assertRaises(SystemExit):
            create_project.safe_repo_name("owner/../ShelfMac")
        with self.assertRaises(SystemExit):
            create_project.safe_repo_name("ShelfMac")
        with self.assertRaises(SystemExit):
            create_project.safe_repo_name("--help/ShelfMac")
        with self.assertRaises(SystemExit):
            create_project.safe_repo_name(f"owner/{'a' * 101}")
        with self.assertRaises(SystemExit):
            create_project.resolve_bundle_id(
                "ShelfMac",
                "owner/ShelfMac",
                "not a bundle id",
            )
        with self.assertRaises(SystemExit):
            create_project.resolve_bundle_id(
                "ShelfMac",
                "owner/ShelfMac",
                f"com.example.{'a' * 244}",
            )

    def test_rejects_project_names_that_are_not_swift_modules(self) -> None:
        with self.assertRaises(SystemExit):
            create_project.safe_project_name("Shelf-Mac")
        with self.assertRaises(SystemExit):
            create_project.safe_project_name("1ShelfMac")
        with self.assertRaises(SystemExit):
            create_project.safe_project_name("class")
        with self.assertRaises(SystemExit):
            create_project.safe_project_name("Self")
        with self.assertRaises(SystemExit):
            create_project.safe_project_name("ModernAppKitPro")
        with self.assertRaises(SystemExit):
            create_project.safe_project_name("Configuration")
        with self.assertRaises(SystemExit):
            create_project.safe_project_name("A" * 129)

    def test_rejects_control_characters_in_display_names(self) -> None:
        with self.assertRaises(SystemExit):
            create_project.resolve_display_name("ShelfMac", "Shelf\nMac")
        with self.assertRaises(SystemExit):
            create_project.resolve_display_name("ShelfMac", "Shelf\x01Mac")
        with self.assertRaises(SystemExit):
            create_project.resolve_display_name("ShelfMac", "A" * 256)


class CustomizationTests(unittest.TestCase):
    def test_customizes_the_complete_template_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "ShelfMac"
            copy_template(repo_root)
            ci_path = repo_root / ".github" / "workflows" / "ci.yml"
            ci_path.write_text(
                ci_path.read_text(encoding="utf-8").replace(
                    "Test appkit-starter tooling",
                    "Test skill tooling",
                ),
                encoding="utf-8",
            )

            create_project.customize_project(
                repo_root,
                project_name="ShelfMac",
                display_name="Shelf & Mac",
                bundle_id="com.example.shelfmac",
            )

            base_config = (repo_root / "Configuration" / "Base.xcconfig").read_text(
                encoding="utf-8"
            )
            info_plist = (
                repo_root / "ShelfMac" / "Resources" / "Info.plist"
            ).read_text(encoding="utf-8")
            project = (
                repo_root / "ShelfMac.xcodeproj" / "project.pbxproj"
            ).read_text(encoding="utf-8")
            environment = (
                repo_root / ".codex" / "environments" / "environment.toml"
            ).read_text(encoding="utf-8")
            mise = (repo_root / "mise.toml").read_text(encoding="utf-8")
            ci = (repo_root / ".github" / "workflows" / "ci.yml").read_text(
                encoding="utf-8"
            )
            agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            remaining_identities = [
                identity
                for path in text_files(repo_root)
                for identity in create_project.TEMPLATE_IDENTITIES
                if identity in path.read_text(encoding="utf-8")
            ]
            remaining_identity_paths = [
                path.relative_to(repo_root).as_posix()
                for path in repo_root.rglob("*")
                for identity in create_project.TEMPLATE_IDENTITIES
                if identity in path.relative_to(repo_root).as_posix()
            ]

            self.assertTrue((repo_root / "ShelfMac").is_dir())
            self.assertTrue((repo_root / "ShelfMacTests").is_dir())
            self.assertTrue((repo_root / "ShelfMac.xcworkspace").is_dir())
            self.assertTrue((repo_root / "ShelfMac.xctestplan").is_file())
            self.assertFalse((repo_root / "skills").exists())
            self.assertIn("DEVELOPMENT_TEAM =\n", base_config)
            self.assertIn("PRODUCT_BUNDLE_IDENTIFIER = com.example.shelfmac", base_config)
            self.assertIn("<string>Shelf &amp; Mac</string>", info_plist)
            self.assertIn('PRODUCT_BUNDLE_IDENTIFIER = "com.example.shelfmac.tests";', project)
            self.assertIn('name = "ShelfMac"', environment)
            self.assertNotIn("test-tooling", mise)
            self.assertNotIn("Test appkit-starter tooling", ci)
            self.assertNotIn("appkit-starter", agents)
            self.assertNotIn("test-tooling", agents)
            self.assertEqual(remaining_identities, [])
            self.assertEqual(remaining_identity_paths, [])

    def test_rejects_rename_collision_before_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "ShelfMac"
            copy_template(repo_root)
            (repo_root / "ShelfMac").mkdir()

            with self.assertRaises(SystemExit):
                create_project.customize_project(
                    repo_root,
                    project_name="ShelfMac",
                    display_name="ShelfMac",
                    bundle_id="com.example.shelfmac",
                )

            self.assertTrue((repo_root / "skills" / "appkit-starter").is_dir())

    def test_rejects_symlinked_template_before_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "ShelfMac"
            outside = Path(tmp) / "outside"
            copy_template(repo_root)
            shutil.rmtree(repo_root / "skills")
            (outside / "appkit-starter").mkdir(parents=True)
            (repo_root / "skills").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(SystemExit):
                create_project.customize_project(
                    repo_root,
                    project_name="ShelfMac",
                    display_name="ShelfMac",
                    bundle_id="com.example.shelfmac",
                )

            self.assertTrue((outside / "appkit-starter").is_dir())

    def test_rejects_unexpected_template_identity_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "ShelfMac"
            copy_template(repo_root)
            (repo_root / "ModernAppKitNotes.md").write_text("Notes\n", encoding="utf-8")

            with self.assertRaises(SystemExit):
                create_project.customize_project(
                    repo_root,
                    project_name="ShelfMac",
                    display_name="ShelfMac",
                    bundle_id="com.example.shelfmac",
                )


class GitHubCreationTests(unittest.TestCase):
    def test_uses_the_template_repository_and_requested_visibility(self) -> None:
        def run_side_effect(command: list[str], cwd: Path | None = None) -> None:
            if command[:3] == ["gh", "repo", "create"]:
                assert cwd is not None
                (cwd / "ShelfMac").mkdir()

        with tempfile.TemporaryDirectory() as tmp, patch.object(
            create_project,
            "run",
            side_effect=run_side_effect,
        ) as run:
            destination = create_project.create_from_github(
                "owner/ShelfMac",
                "private",
                Path(tmp),
            )

        self.assertEqual(destination.name, "ShelfMac")
        run.assert_any_call(
            [
                "gh",
                "repo",
                "create",
                "--private",
                "--template",
                "Zach677/Modern.AppKit",
                "--clone",
                "--",
                "owner/ShelfMac",
            ],
            cwd=Path(tmp),
        )

    def test_verifies_the_fixed_github_source(self) -> None:
        with patch.object(create_project, "run") as run:
            create_project.verify_github_access()

        run.assert_any_call(
            ["gh", "auth", "status", "--active", "--hostname", "github.com"]
        )
        run.assert_any_call(["gh", "repo", "view", "Zach677/Modern.AppKit"])

    def test_preflights_before_remote_creation(self) -> None:
        with (
            patch.object(create_project, "run") as run,
            patch.object(create_project, "customize_project") as customize,
            patch.object(create_project, "verify_repo") as verify,
        ):
            create_project.preflight_project(
                "ShelfMac",
                "Shelf Mac",
                "com.example.shelfmac",
                "test",
            )

        clone_command = run.call_args.args[0]
        self.assertEqual(clone_command[:4], ["gh", "repo", "clone", "Zach677/Modern.AppKit"])
        repo_root = Path(clone_command[4])
        customize.assert_called_once_with(
            repo_root,
            "ShelfMac",
            "Shelf Mac",
            "com.example.shelfmac",
        )
        verify.assert_called_once_with(repo_root, "test")


class CommandWorkflowTests(unittest.TestCase):
    def test_defaults_to_test_verification(self) -> None:
        with patch(
            "sys.argv",
            [
                "create_project.py",
                "--project-name",
                "ShelfMac",
                "--repo",
                "owner/ShelfMac",
                "--parent-dir",
                "/tmp",
            ],
        ):
            args = create_project.parse_args()

        self.assertEqual(args.verify, "test")

    def test_reports_partial_creation_without_deleting_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "ShelfMac"
            args = SimpleNamespace(
                project_name="ShelfMac",
                display_name=None,
                repo="owner/ShelfMac",
                bundle_id=None,
                parent_dir=tmp,
                visibility="private",
                verify="test",
            )
            stderr = io.StringIO()
            with (
                patch.object(create_project, "parse_args", return_value=args),
                patch.object(
                    create_project,
                    "create_from_github",
                    return_value=repo_root,
                ),
                patch.object(create_project, "verify_github_access"),
                patch.object(create_project, "preflight_project"),
                patch.object(
                    create_project,
                    "customize_project",
                    side_effect=SystemExit(1),
                ),
                redirect_stderr(stderr),
                self.assertRaises(SystemExit),
            ):
                create_project.main()

        self.assertIn("https://github.com/owner/ShelfMac", stderr.getvalue())
        self.assertIn(str(repo_root), stderr.getvalue())
        self.assertIn("did not delete", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
