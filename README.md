# Modern.AppKit

> Agent-native, programmatic AppKit starter for ordinary macOS window apps.

## Create a Project

Install the skill for Codex, Claude Code, or another skill-aware Agent:

```bash
npx skills add Zach677/Modern.AppKit --skill appkit-starter -g -y
```

Then ask the Agent to use `$appkit-starter`:

- `Use $appkit-starter to create a new private AppKit app repo named ShelfMac.`
- `Use $appkit-starter to create an AppKit app named ShelfMac with the display name Shelf Mac.`

The skill creates fresh repositories only. Existing-repository adoption, SwiftUI migration, menu-bar apps, and multi-window architecture are outside its current scope.

## Starter

- Pure AppKit with `main.swift`, `AppDelegate`, `NSWindow`, and `RootViewController`.
- One standard window and a programmatic App, Edit, and Window menu bar.
- An Xcode workspace, shared test plan, and hosted Swift Testing target.
- `AppPreferences` for starter-level configuration.
- App sandbox and hardened runtime settings.
- macOS 15.0 and Swift 6.0 defaults.

`NSWindowController` is intentionally absent. Add it when the app must recreate, reopen, or coordinate windows.

## Development

Open `ModernAppKit.xcworkspace`, or use:

```bash
mise build
mise test
mise run
mise format-lint
```

Run `mise test-tooling` after changing `skills/appkit-starter`. CI runs the build, app tests, tooling tests, and formatting gate.

Local signing and bundle overrides belong in the ignored `Configuration/Developer*.xcconfig` files.

## Requirements

- Xcode 16 or later with the macOS 15 SDK
- `mise`
- Node.js with `npx`, plus GitHub CLI (`gh`) for skill-driven project creation
- `xcbeautify` (optional)

## License

Modern.AppKit is licensed under the MIT License. See [LICENSE](LICENSE).
