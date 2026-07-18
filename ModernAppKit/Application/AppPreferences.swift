import Foundation

struct AppConfiguration: Equatable, Sendable {
    let bundleIdentifier: String
    let displayName: String
}

final class AppPreferences: Sendable {
    let configuration: AppConfiguration

    init(configuration: AppConfiguration) {
        self.configuration = configuration
    }
}
