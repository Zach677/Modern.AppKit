---
name: appkit-starter
description: Create fresh programmatic AppKit macOS app repositories from `Zach677/Modern.AppKit`. Use when the user asks an AI coding agent to start a new ordinary window-based AppKit app with an Xcode workspace, hosted Swift Testing, programmatic menus, and mise build automation. Do not use for existing-repository adoption, SwiftUI migration, menu-bar apps, utilities, or multi-window architecture.
---

# AppKit Starter

## Contract

Use this skill as the user-facing workflow. Treat `scripts/create_project.py` as a deterministic backend, not the primary interface.

- Create only fresh repositories from `Zach677/Modern.AppKit`.
- Stop if the target GitHub repository or local destination already exists.
- Preserve the starter's `main.swift` -> `AppDelegate` -> `NSWindow` -> `RootViewController` path.
- Keep the standard single-window AppKit baseline, programmatic menu bar, sandbox, hardened runtime settings, tests, and mise tasks.
- Do not add SwiftUI, `NSWindowController`, multiple windows, menu-bar behavior, custom chrome, packaging, releases, or existing-repo adoption.

## Workflow

1. Confirm the request is for a fresh ordinary AppKit macOS app.
2. Collect only missing inputs:
   - Internal project name.
   - Optional display name; default to the project name verbatim.
   - GitHub repository in `owner/name` form.
   - Local parent directory for the clone.
   - Optional bundle identifier; otherwise derive a `com.example.*` identifier.
   - Visibility; default to private.
   - Verification level; default to test.
3. Confirm the target GitHub repository and local destination do not exist.
4. Run `scripts/create_project.py` with the confirmed inputs. It must pass customization and the selected verification in a temporary clone before creating the target GitHub repository.
5. Inspect the generated diff and verify that no `ModernAppKit`, `Modern.AppKit`, or `modern-appkit` template identity remains outside Git metadata.
6. Read the complete build or test log. Do not treat exit code zero alone as proof.
7. Finish commit and push only when the user's request authorizes the new repository workflow.

## Backend

Run from this skill directory or pass an absolute script path:

```bash
python3 scripts/create_project.py \
    --project-name ShelfMac \
    --repo owner/ShelfMac \
    --parent-dir /path/to/projects \
    --bundle-id com.example.shelfmac \
    --visibility private \
    --verify test
```

Supported verification values are `none`, `build`, and `test`. The backend requires `gh`, `mise`, Git, and an Xcode installation capable of building the template.

## Report

State the created local path and GitHub repository, resolved project/display names, bundle identifier, team-neutral signing choice, verification command and result, and any Git action not performed.
