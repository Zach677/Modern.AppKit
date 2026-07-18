# Project Overview

## App Shape

- This is a pure AppKit starter for an ordinary single-window macOS app.
- Keep the entry path as `ModernAppKit/Application/main.swift` -> `AppDelegate.swift` -> `NSWindow` -> `RootViewController.swift`.
- `AppDelegate` owns the initial window, bootstraps `AppPreferences`, and installs the programmatic menu bar.
- Do not introduce SwiftUI by default.
- Add `NSWindowController` only when a window must be recreated, reopened after closing, or coordinated with another window.

## Structure

- `ModernAppKit/` contains app source and bundled resources.
- `ModernAppKit.xcworkspace/` is the default Xcode entrypoint.
- `Configuration/` owns shared signing, bundle, and version settings.
- `ModernAppKitTests/` contains hosted Swift Testing tests.
- `Resources/DevKit/scripts/` contains reusable build tooling.
- `script/build_and_run.sh` is the stable kill, build, and launch entrypoint behind `mise run` and the Codex Run action.

### Application

- Keep lifecycle and app-wide configuration in `Application/`.
- Thread starter-level configuration through `AppPreferences`.
- Do not put feature state, persistence, or view composition in `AppDelegate`.

### Interface

- Keep the initial shell in `Interface/Root/`.
- Add feature-specific controllers under dedicated `Interface/<Feature>/` folders.
- Create `Interface/Common/` only after two production consumers need the same primitive.

### Backend

- Add `Backend/` when the app gains domain services, persistence, API clients, or cross-feature state ownership.
- Prefer dependency injection over app-owned singletons.

## AppKit Rules

- Keep `main.swift`; do not switch to a SwiftUI `App` entrypoint.
- Build the main menu programmatically. Keep App, Edit, and Window responder-chain actions intact.
- Use standard titled, closable, miniaturizable, resizable windows by default.
- Keep system title bars and backgrounds until a product requirement needs custom chrome.
- Use sheets for document-modal work and panels only for genuine utility surfaces.
- Keep window and view-controller types main-actor isolated.
- Do not add menu-bar, Dock-tile, overlay, borderless, or transparent window behavior to the starter baseline.

## Configuration

- Keep the reusable starter team-neutral.
- Default local builds use ad-hoc signing.
- Put personal signing and bundle overrides in ignored developer configuration files.
- Keep versions in `Configuration/Version.xcconfig`.
- Replace the starter's developer-tools app category when a generated product belongs to another category.
- Keep the macOS deployment target, Swift version, sandbox, hardened runtime, and Info.plist wiring in `project.pbxproj`.

## Localization

- Use `String(localized:)` for user-facing strings.
- Keep natural English keys with complete `en` and `zh-Hans` translations in `ModernAppKit/Resources/Localizable.xcstrings`.
- Preserve positional format specifiers when translating formatted strings.

## Testing

- Prefer Swift Testing.
- Test behavior and dependency wiring before presentation details.
- Keep tests under the closest feature or subdomain folder.
- Run `mise test` after app or test changes.

## Build Workflow

- Use `mise build`, `mise test`, and `mise run` for routine workflows.
- Do not invoke `xcodebuild` directly when a mise task covers the operation.
- Treat the full log as the source of truth; a zero exit code alone is insufficient.
- Run `mise format-lint` before handoff.
- `mise run` must launch the foreground `.app` bundle, not the raw executable.

## Documentation Sync

- Update this file and `README.md` when the lifecycle, structure, or workflow contract changes.
