import Foundation

extension AppPreferences {
    static func bootstrap(bundle: Bundle = .main) -> AppPreferences {
        let bundleIdentifier = bundle.bundleIdentifier ?? "com.example.app"
        let displayName =
            (bundle.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String)?
                .trimmingCharacters(in: .whitespacesAndNewlines)
                ?? (bundle.object(forInfoDictionaryKey: kCFBundleNameKey as String) as? String)?
                .trimmingCharacters(in: .whitespacesAndNewlines)
                ?? "AppKit App"

        return AppPreferences(
            configuration: AppConfiguration(
                bundleIdentifier: bundleIdentifier,
                displayName: displayName
            )
        )
    }
}
