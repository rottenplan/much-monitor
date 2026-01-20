import os
import Quartz
import Cocoa
from PyObjCTools import AppHelper
from profile_manager import ProfileManager

class MuchMonitorMenuBar(Cocoa.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        # Create the status bar item
        self.statusbar = Cocoa.NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(Cocoa.NSVariableStatusItemLength)
        
        # Set icon/label
        self.statusitem.button().setTitle_("MuchCalib")
        
        # Create the menu
        self.menu = Cocoa.NSMenu.alloc().init()
        self.updateMenu()
        self.statusitem.setMenu_(self.menu)

    def updateMenu(self):
        self.menu.removeAllItems()
        
        # Title
        titleItem = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Much Monitor Control", None, "")
        titleItem.setEnabled_(False)
        self.menu.addItem_(titleItem)
        
        self.menu.addItem_(Cocoa.NSMenuItem.separatorItem())
        
        # List Profiles
        profiles = ProfileManager.list_installed_profiles()
        if not profiles:
            noneItem = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("No Profiles Found", None, "")
            noneItem.setEnabled_(False)
            self.menu.addItem_(noneItem)
        else:
            for p in profiles:
                # Use filename without extension as the display name and switch target
                display_name = os.path.basename(p).replace(".icc", "").replace(".icm", "")
                item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    display_name, "switchProfile:", ""
                )
                item.setTarget_(self)
                item.setRepresentedObject_(p)
                self.menu.addItem_(item)

        self.menu.addItem_(Cocoa.NSMenuItem.separatorItem())
        
        # System Settings Shortcut
        settingsItem = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Open Display Settings...", "openSettings:", "")
        settingsItem.setTarget_(self)
        self.menu.addItem_(settingsItem)

        # Refresh
        refreshItem = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Refresh List", "refresh:", "")
        refreshItem.setTarget_(self)
        self.menu.addItem_(refreshItem)
        
        # Quit
        quitItem = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        self.menu.addItem_(quitItem)

    def switchProfile_(self, sender):
        profile_path = sender.representedObject()
        # display_id=None tells ProfileManager to use Main Display
        if ProfileManager.set_display_profile(None, profile_path):
            print(f"Switched to {profile_path}")
        else:
            print("Failed to switch profile")

    def openSettings_(self, sender):
        import subprocess
        subprocess.run(["open", "x-apple.systempreferences:com.apple.Displays-Settings.extension"])

    def refresh_(self, sender):
        self.updateMenu()

if __name__ == "__main__":
    app = Cocoa.NSApplication.sharedApplication()
    
    # This prevents the app from appearing in the Dock but allows status bar items
    app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)
    
    delegate = MuchMonitorMenuBar.alloc().init()
    app.setDelegate_(delegate)
    
    print("Menu Bar Helper started...")
    AppHelper.runEventLoop()
