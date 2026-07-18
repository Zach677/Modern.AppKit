import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private let defaultContentSize = NSSize(width: 900, height: 600)
    private let minimumContentSize = NSSize(width: 640, height: 420)
    private var window: NSWindow?

    func applicationDidFinishLaunching(_: Notification) {
        let preferences = AppPreferences.bootstrap()
        let displayName = preferences.configuration.displayName

        installMainMenu(displayName: displayName)

        let window = NSWindow(
            contentRect: NSRect(origin: .zero, size: defaultContentSize),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = displayName
        window.contentViewController = RootViewController(preferences: preferences)
        window.contentMinSize = minimumContentSize
        window.setContentSize(defaultContentSize)
        window.center()

        self.window = window
        window.makeKeyAndOrderFront(nil)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_: NSApplication) -> Bool {
        true
    }
}

private extension AppDelegate {
    func installMainMenu(displayName: String) {
        let mainMenu = NSMenu()
        let applicationMenuItem = NSMenuItem()
        let editMenuItem = NSMenuItem()
        let windowMenuItem = NSMenuItem()

        mainMenu.addItem(applicationMenuItem)
        mainMenu.addItem(editMenuItem)
        mainMenu.addItem(windowMenuItem)

        let applicationMenu = NSMenu(title: displayName)
        applicationMenu.addItem(
            withTitle: String(format: String(localized: "About %@"), displayName),
            action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)),
            keyEquivalent: ""
        )
        applicationMenu.addItem(.separator())

        let servicesItem = NSMenuItem(
            title: String(localized: "Services"),
            action: nil,
            keyEquivalent: ""
        )
        let servicesMenu = NSMenu(title: String(localized: "Services"))
        servicesItem.submenu = servicesMenu
        applicationMenu.addItem(servicesItem)
        applicationMenu.addItem(.separator())

        applicationMenu.addItem(
            withTitle: String(format: String(localized: "Hide %@"), displayName),
            action: #selector(NSApplication.hide(_:)),
            keyEquivalent: "h"
        )
        let hideOthersItem = applicationMenu.addItem(
            withTitle: String(localized: "Hide Others"),
            action: #selector(NSApplication.hideOtherApplications(_:)),
            keyEquivalent: "h"
        )
        hideOthersItem.keyEquivalentModifierMask = [.command, .option]
        applicationMenu.addItem(
            withTitle: String(localized: "Show All"),
            action: #selector(NSApplication.unhideAllApplications(_:)),
            keyEquivalent: ""
        )
        applicationMenu.addItem(.separator())
        applicationMenu.addItem(
            withTitle: String(format: String(localized: "Quit %@"), displayName),
            action: #selector(NSApplication.terminate(_:)),
            keyEquivalent: "q"
        )
        applicationMenuItem.submenu = applicationMenu

        let editMenu = NSMenu(title: String(localized: "Edit"))
        editMenu.addItem(
            withTitle: String(localized: "Undo"),
            action: Selector(("undo:")),
            keyEquivalent: "z"
        )
        let redoItem = editMenu.addItem(
            withTitle: String(localized: "Redo"),
            action: Selector(("redo:")),
            keyEquivalent: "z"
        )
        redoItem.keyEquivalentModifierMask = [.command, .shift]
        editMenu.addItem(.separator())
        editMenu.addItem(
            withTitle: String(localized: "Cut"),
            action: #selector(NSText.cut(_:)),
            keyEquivalent: "x"
        )
        editMenu.addItem(
            withTitle: String(localized: "Copy"),
            action: #selector(NSText.copy(_:)),
            keyEquivalent: "c"
        )
        editMenu.addItem(
            withTitle: String(localized: "Paste"),
            action: #selector(NSText.paste(_:)),
            keyEquivalent: "v"
        )
        editMenu.addItem(
            withTitle: String(localized: "Select All"),
            action: #selector(NSText.selectAll(_:)),
            keyEquivalent: "a"
        )
        editMenuItem.title = String(localized: "Edit")
        editMenuItem.submenu = editMenu

        let windowMenu = NSMenu(title: String(localized: "Window"))
        windowMenu.addItem(
            withTitle: String(localized: "Minimize"),
            action: #selector(NSWindow.performMiniaturize(_:)),
            keyEquivalent: "m"
        )
        windowMenu.addItem(
            withTitle: String(localized: "Zoom"),
            action: #selector(NSWindow.performZoom(_:)),
            keyEquivalent: ""
        )
        windowMenu.addItem(.separator())
        windowMenu.addItem(
            withTitle: String(localized: "Bring All to Front"),
            action: #selector(NSApplication.arrangeInFront(_:)),
            keyEquivalent: ""
        )
        windowMenuItem.title = String(localized: "Window")
        windowMenuItem.submenu = windowMenu

        NSApp.servicesMenu = servicesMenu
        NSApp.windowsMenu = windowMenu
        NSApp.mainMenu = mainMenu
    }
}
