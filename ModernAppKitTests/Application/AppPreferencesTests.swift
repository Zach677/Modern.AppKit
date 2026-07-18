import Foundation
@testable import ModernAppKit
import Testing

@Suite(.serialized)
struct AppPreferencesTests {
    @Test
    func bootstrapUsesProvidedBundleMetadata() {
        let bundle = Bundle(for: BundleSentinel.self)

        let preferences = AppPreferences.bootstrap(bundle: bundle)

        #expect(preferences.configuration.bundleIdentifier == (bundle.bundleIdentifier ?? "com.example.app"))
        #expect(!preferences.configuration.displayName.isEmpty)
    }

    @Test
    @MainActor
    func rootViewControllerUsesInjectedDisplayName() {
        let preferences = AppPreferences(
            configuration: AppConfiguration(
                bundleIdentifier: "com.example.tests",
                displayName: "Template App"
            )
        )

        let viewController = RootViewController(preferences: preferences)
        viewController.loadView()
        viewController.viewDidLoad()

        #expect(viewController.title == "Template App")
    }
}

private final class BundleSentinel {}
