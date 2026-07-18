# Modern.AppKit

> Agent-native, programmatic AppKit starter for ordinary macOS window apps.

Modern.AppKit provides the smallest production-shaped AppKit baseline: a native Xcode workspace, explicit application lifecycle, one standard window, a programmatic menu bar, dependency injection, hosted Swift Testing, and `mise` build automation.

## Starter Contract

- Pure AppKit. SwiftUI is not linked by default.
- `main.swift` starts `NSApplication` on the main actor.
- `AppDelegate` owns the first `NSWindow` and terminates after it closes.
- `RootViewController` owns the initial programmatic view hierarchy.
- App, Edit, and Window menus are created in code.
- `AppPreferences` is the starter-level configuration surface.
- The app sandbox is enabled; hardened runtime is configured for properly signed builds.
- macOS 15.0 and Swift 6.0 are the default targets.

`NSWindowController` is intentionally absent. Add it when a window must be recreated, reopened after closing, or coordinated alongside another window.

## Workflow

Open `ModernAppKit.xcworkspace` in Xcode, or use:

```bash
mise build
mise test
mise run
mise format-lint
```

Local signing and bundle overrides belong in the ignored `Configuration/Developer*.xcconfig` files.

GitHub Actions runs `mise build`, `mise test`, and `mise format-lint` on pushes and pull requests.

## Requirements

- Xcode 16 or later with the macOS 15 SDK
- `mise` (`mise install` provisions the pinned SwiftFormat tool)
- `xcbeautify` (optional)

## License

Modern.AppKit is licensed under the MIT License. See `LICENSE`.
