#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape


DEFAULT_TEMPLATE_REPO = "Zach677/Modern.AppKit"
TEMPLATE_IDENTITIES = ("ModernAppKit", "Modern.AppKit", "modern-appkit")
SKIP_DIR_NAMES = {".git", ".DerivedData", "__pycache__", "xcuserdata"}
RESERVED_PROJECT_NAMES = {"configuration", "resources", "script", "skills"}
RESERVED_SWIFT_MODULE_NAMES = {"Any", "Self"}


def run(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def safe_project_name(value: str) -> str:
    value = value.strip()
    if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", value):
        raise SystemExit(
            "Project name must be an UpperCamelCase Swift module identifier."
        )
    if value in RESERVED_SWIFT_MODULE_NAMES:
        raise SystemExit("Project name cannot be a Swift reserved word.")
    if value.casefold() in RESERVED_PROJECT_NAMES:
        raise SystemExit("Project name conflicts with a starter root directory.")
    if "modernappkit" in value.casefold():
        raise SystemExit("Project name cannot contain the template identity.")
    if len(value.encode("utf-8")) > 128:
        raise SystemExit("Project name must be at most 128 UTF-8 bytes.")
    return value


def safe_repo_name(value: str) -> str:
    value = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise SystemExit("Repository must use the form 'owner/name'.")
    parts = value.split("/")
    if any(part in {".", ".."} or part.startswith("-") for part in parts):
        raise SystemExit("Repository components cannot be options, '.' or '..'.")
    if any(len(part.encode("utf-8")) > 100 for part in parts):
        raise SystemExit("Repository components must be at most 100 UTF-8 bytes.")
    return value


def repo_basename(repo_name: str) -> str:
    return repo_name.rsplit("/", 1)[-1]


def resolve_display_name(project_name: str, display_name: str | None) -> str:
    if display_name is None:
        return project_name
    display_name = display_name.strip()
    if not display_name:
        raise SystemExit("Display name cannot be empty.")
    if any(
        not (
            0x20 <= ord(character) <= 0xD7FF
            or 0xE000 <= ord(character) <= 0xFFFD
            or 0x10000 <= ord(character) <= 0x10FFFF
        )
        for character in display_name
    ):
        raise SystemExit("Display name cannot contain control characters.")
    if len(display_name.encode("utf-8")) > 255:
        raise SystemExit("Display name must be at most 255 UTF-8 bytes.")
    return display_name


def bundle_component(value: str) -> str:
    component = re.sub(r"[^A-Za-z0-9]+", "", value).lower()
    if not component:
        raise SystemExit("Unable to derive bundle identifier component.")
    return component


def resolve_bundle_id(project_name: str, repo_name: str, bundle_id: str | None) -> str:
    value = bundle_id.strip() if bundle_id else None
    if value is None:
        value = f"com.example.{bundle_component(repo_basename(repo_name) or project_name)}"
    if not re.fullmatch(r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value):
        raise SystemExit("Bundle identifier must use reverse-DNS components.")
    if len(value.encode("utf-8")) > 255:
        raise SystemExit("Bundle identifier must be at most 255 UTF-8 bytes.")
    return value


def should_skip(path: Path, repo_root: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.relative_to(repo_root).parts)


def require_repo_path(repo_root: Path, path: Path) -> None:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve(strict=False)
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise SystemExit(f"Path escapes repository: {path}") from error
    if relative == Path("."):
        raise SystemExit("Refusing to mutate the repository root.")


def ensure_no_symlinks(repo_root: Path) -> None:
    for path in repo_root.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"Template contains unsupported symlink: {path}")


def is_text_file(path: Path) -> bool:
    if path.is_symlink():
        return False
    try:
        data = path.read_bytes()
        data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return b"\0" not in data


def detect_template_markers(repo_root: Path) -> dict[str, str]:
    projects = sorted(repo_root.glob("*.xcodeproj"))
    workspaces = sorted(repo_root.glob("*.xcworkspace"))
    test_plans = sorted(repo_root.glob("*.xctestplan"))
    source_dirs = sorted(repo_root.glob("*/Resources/Info.plist"))
    test_dirs = sorted(
        path for path in repo_root.iterdir() if path.is_dir() and path.name.endswith("Tests")
    )
    if not all(
        len(paths) == 1
        for paths in (projects, workspaces, test_plans, source_dirs, test_dirs)
    ):
        raise SystemExit(
            "Expected one root project, workspace, test plan, app source, and test directory."
        )
    return {
        "project_name": projects[0].stem,
        "workspace_name": workspaces[0].stem,
        "test_plan_name": test_plans[0].stem,
        "source_name": source_dirs[0].relative_to(repo_root).parts[0],
        "tests_name": test_dirs[0].name,
    }


def replace_across_repo(repo_root: Path, replacements: list[tuple[str, str]]) -> None:
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or should_skip(path, repo_root) or not is_text_file(path):
            continue
        original = path.read_text(encoding="utf-8")
        updated = original
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != original:
            require_repo_path(repo_root, path)
            path.write_text(updated, encoding="utf-8")


def replace_assignment(repo_root: Path, path: Path, key: str, value: str) -> None:
    require_repo_path(repo_root, path)
    content = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        rf"^{re.escape(key)}\s*=.*$",
        f"{key} = {value}",
        content,
        flags=re.MULTILINE,
    )
    if count == 0:
        raise SystemExit(f"Failed to update {key} in {path}.")
    path.write_text(updated, encoding="utf-8")


def replace_literal(repo_root: Path, path: Path, old: str, new: str) -> None:
    require_repo_path(repo_root, path)
    content = path.read_text(encoding="utf-8")
    if old not in content:
        raise SystemExit(f"Failed to find expected text in {path}: {old}")
    path.write_text(content.replace(old, new), encoding="utf-8")


def rename_path(repo_root: Path, path: Path, new_name: str) -> Path:
    require_repo_path(repo_root, path)
    if path.name == new_name:
        return path
    target = path.with_name(new_name)
    require_repo_path(repo_root, target)
    if target.exists():
        raise SystemExit(f"Cannot rename {path}; destination exists: {target}")
    path.rename(target)
    return target


def ensure_display_name(repo_root: Path, info_plist: Path, display_name: str) -> None:
    require_repo_path(repo_root, info_plist)
    content = info_plist.read_text(encoding="utf-8")
    key = "<key>CFBundleDisplayName</key>"
    value = f"{key}\n\t<string>{escape(display_name)}</string>"
    updated, count = re.subn(
        rf"{re.escape(key)}\s*<string>.*?</string>",
        value,
        content,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise SystemExit(f"Failed to update CFBundleDisplayName in {info_plist}.")
    info_plist.write_text(updated, encoding="utf-8")


def remove_path(repo_root: Path, path: Path) -> None:
    if not path.exists():
        return
    require_repo_path(repo_root, path)
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def prune_template_files(repo_root: Path) -> None:
    paths_and_patterns = (
        (
            repo_root / "mise.toml",
            r"\n\[tasks\.test-tooling\]\n.*?(?=\n\[tasks\.|\Z)",
        ),
        (
            repo_root / ".github" / "workflows" / "ci.yml",
            r"\n      - name: [^\n]+\n"
            r"        run: mise test-tooling\n",
        ),
        (
            repo_root / "AGENTS.md",
            r"\n## AppKit Starter Skill\n.*?(?=\n## |\Z)",
        ),
    )
    updates: list[tuple[Path, str]] = []
    for path, pattern in paths_and_patterns:
        require_repo_path(repo_root, path)
        content = path.read_text(encoding="utf-8")
        updated, count = re.subn(pattern, "", content, count=1, flags=re.DOTALL)
        if count != 1:
            raise SystemExit(f"Failed to find template-only block in {path}.")
        updates.append((path, updated))
    for path, content in updates:
        path.write_text(content, encoding="utf-8")

    remove_path(repo_root, repo_root / "skills" / "appkit-starter")
    for path in sorted(repo_root.rglob("xcuserdata"), reverse=True):
        if path.is_dir():
            require_repo_path(repo_root, path)
            shutil.rmtree(path)
    skills_dir = repo_root / "skills"
    if skills_dir.exists() and not any(skills_dir.iterdir()):
        require_repo_path(repo_root, skills_dir)
        skills_dir.rmdir()


def validate_rename_targets(
    repo_root: Path,
    renames: list[tuple[Path, Path]],
) -> None:
    for source, target in renames:
        require_repo_path(repo_root, source)
        require_repo_path(repo_root, target)
        if len(target.name.encode("utf-8")) > 255:
            raise SystemExit(f"Generated path component is too long: {target.name}")
        for sibling in source.parent.iterdir():
            if sibling == source:
                continue
            if sibling.name.casefold() == target.name.casefold():
                raise SystemExit(f"Generated path conflicts with existing path: {target}")
        if source.name != target.name and source.name.casefold() == target.name.casefold():
            raise SystemExit(f"Case-only rename is unsupported: {source} -> {target}")


def ensure_no_template_identities(repo_root: Path) -> None:
    for path in sorted(repo_root.rglob("*")):
        if should_skip(path, repo_root):
            continue
        relative_path = path.relative_to(repo_root).as_posix()
        for identity in TEMPLATE_IDENTITIES:
            if identity in relative_path:
                raise SystemExit(f"Template identity remains in path: {relative_path}")
        if not path.is_file() or not is_text_file(path):
            continue
        content = path.read_text(encoding="utf-8")
        for identity in TEMPLATE_IDENTITIES:
            if identity in content:
                raise SystemExit(f"Template identity remains in file: {relative_path}")


def write_generated_readme(
    repo_root: Path,
    project_name: str,
    display_name: str,
    bundle_id: str,
) -> None:
    readme = repo_root / "README.md"
    require_repo_path(repo_root, readme)
    content = f"""# {display_name}

`{display_name}` is a programmatic AppKit macOS app with an ordinary single-window baseline.

## Project Layout

- `{project_name}/`: app source and bundled resources
- `{project_name}Tests/`: hosted Swift Testing tests
- `Configuration/`: shared signing, bundle, and version settings
- `Resources/DevKit/scripts/`: log-aware Xcode build wrapper
- `{project_name}.xcworkspace`: default Xcode entrypoint
- `{project_name}.xctestplan`: shared test plan

## Development

```bash
mise build
mise test
mise run
mise format-lint
```

The app uses AppKit through `main.swift`, `AppDelegate`, a standard `NSWindow`, and `RootViewController`. The application menu is programmatic, and SwiftUI is not linked by default.

## Signing

Shared defaults live in `Configuration/Base.xcconfig`:

```xcconfig
DEVELOPMENT_TEAM =
PRODUCT_BUNDLE_IDENTIFIER = {bundle_id}
```

Keep personal overrides in the ignored `Configuration/Developer*.xcconfig` files.
"""
    readme.write_text(content, encoding="utf-8")


def customize_project(
    repo_root: Path,
    project_name: str,
    display_name: str,
    bundle_id: str,
) -> None:
    project_name = safe_project_name(project_name)
    display_name = resolve_display_name(project_name, display_name)
    ensure_no_symlinks(repo_root)
    markers = detect_template_markers(repo_root)
    tests_name = f"{project_name}Tests"
    replacement_map = dict(
        [
            (markers["tests_name"], tests_name),
            (markers["project_name"], project_name),
            (markers["source_name"], project_name),
            ("Modern.AppKit", project_name),
            ("modern-appkit", project_name.lower()),
        ]
    )
    replacements = sorted(
        replacement_map.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    source_dir = repo_root / markers["source_name"]
    tests_dir = repo_root / markers["tests_name"]
    project_dir = repo_root / f'{markers["project_name"]}.xcodeproj'
    workspace_dir = repo_root / f'{markers["workspace_name"]}.xcworkspace'
    test_plan = repo_root / f'{markers["test_plan_name"]}.xctestplan'
    scheme = (
        project_dir
        / "xcshareddata"
        / "xcschemes"
        / f'{markers["project_name"]}.xcscheme'
    )
    renames = [
        (source_dir, source_dir.with_name(project_name)),
        (tests_dir, tests_dir.with_name(tests_name)),
        (project_dir, project_dir.with_name(f"{project_name}.xcodeproj")),
        (workspace_dir, workspace_dir.with_name(f"{project_name}.xcworkspace")),
        (test_plan, test_plan.with_name(f"{project_name}.xctestplan")),
    ]
    if scheme.exists():
        renames.append((scheme, scheme.with_name(f"{project_name}.xcscheme")))
    validate_rename_targets(repo_root, renames)

    prune_template_files(repo_root)
    replace_across_repo(repo_root, replacements)
    replace_assignment(
        repo_root,
        repo_root / "Configuration" / "Base.xcconfig",
        "PRODUCT_BUNDLE_IDENTIFIER",
        bundle_id,
    )

    renamed_source = rename_path(repo_root, source_dir, project_name)
    rename_path(repo_root, tests_dir, tests_name)
    ensure_display_name(
        repo_root,
        renamed_source / "Resources" / "Info.plist",
        display_name,
    )
    if scheme.exists():
        rename_path(repo_root, scheme, f"{project_name}.xcscheme")
    renamed_project = rename_path(repo_root, project_dir, f"{project_name}.xcodeproj")
    replace_literal(
        repo_root,
        renamed_project / "project.pbxproj",
        'PRODUCT_BUNDLE_IDENTIFIER = "com.example.$(PRODUCT_NAME:rfc1034identifier)";',
        f'PRODUCT_BUNDLE_IDENTIFIER = "{bundle_id}.tests";',
    )
    rename_path(repo_root, workspace_dir, f"{project_name}.xcworkspace")
    rename_path(repo_root, test_plan, f"{project_name}.xctestplan")
    write_generated_readme(
        repo_root,
        project_name,
        display_name,
        bundle_id,
    )
    ensure_no_template_identities(repo_root)


def create_from_github(
    repo_name: str,
    visibility: str,
    parent_dir: Path,
) -> Path:
    parent_dir.mkdir(parents=True, exist_ok=True)
    local_dir = parent_dir / repo_basename(repo_name)
    if local_dir.exists():
        raise SystemExit(f"Local destination already exists: {local_dir}")

    run(
        [
            "gh",
            "repo",
            "create",
            f"--{visibility}",
            "--template",
            DEFAULT_TEMPLATE_REPO,
            "--clone",
            "--",
            repo_name,
        ],
        cwd=parent_dir,
    )
    if not local_dir.is_dir():
        raise SystemExit(f"GitHub CLI did not create the local clone: {local_dir}")
    return local_dir


def verify_github_access() -> None:
    run(["gh", "auth", "status", "--active", "--hostname", "github.com"])
    run(["gh", "repo", "view", DEFAULT_TEMPLATE_REPO])


def verify_repo(repo_root: Path, mode: str) -> None:
    if mode == "none":
        return
    run(["mise", "trust", "mise.toml"], cwd=repo_root)
    run(["mise", "build" if mode == "build" else "test"], cwd=repo_root)


def preflight_project(
    project_name: str,
    display_name: str,
    bundle_id: str,
    verify_mode: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="appkit-starter-") as tmp:
        repo_root = Path(tmp) / "template"
        run(
            [
                "gh",
                "repo",
                "clone",
                DEFAULT_TEMPLATE_REPO,
                str(repo_root),
                "--",
                "--depth=1",
            ]
        )
        customize_project(repo_root, project_name, display_name, bundle_id)
        verify_repo(repo_root, verify_mode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--display-name")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--bundle-id")
    parser.add_argument("--parent-dir", required=True)
    parser.add_argument(
        "--visibility",
        choices=["private", "public", "internal"],
        default="private",
    )
    parser.add_argument(
        "--verify",
        choices=["none", "build", "test"],
        default="test",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_name = safe_project_name(args.project_name)
    repo_name = safe_repo_name(args.repo)
    display_name = resolve_display_name(project_name, args.display_name)
    bundle_id = resolve_bundle_id(project_name, repo_name, args.bundle_id)
    parent_dir = Path(args.parent_dir).expanduser().resolve()
    repo_root = parent_dir / repo_basename(repo_name)
    verify_github_access()
    preflight_project(
        project_name,
        display_name,
        bundle_id,
        args.verify,
    )
    try:
        repo_root = create_from_github(
            repo_name,
            args.visibility,
            parent_dir,
        )
        customize_project(
            repo_root,
            project_name,
            display_name,
            bundle_id,
        )
        verify_repo(repo_root, args.verify)
    except BaseException:
        print("Project creation did not complete.", file=sys.stderr)
        print(f"Check GitHub repository: https://github.com/{repo_name}", file=sys.stderr)
        print(f"Check local path: {repo_root}", file=sys.stderr)
        print("The script did not delete either location.", file=sys.stderr)
        raise
    print(f"Created project at: {repo_root}")
    print(f"Project name: {project_name}")
    print(f"Display name: {display_name}")
    print(f"Bundle identifier: {bundle_id}")
    print("Development team: (not set)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
