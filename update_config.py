import plistlib
import os

CONFIG_PATH = "/Volumes/EFI/EFI/OC/config.plist"
BACKUP_PATH = "/Volumes/EFI/EFI/OC/config.plist.bak"

NEW_KEXTS = [
    {
        "Arch": "Any",
        "BundlePath": "BlueToolFixup.kext",
        "Comment": "Bluetooth Fixup",
        "Enabled": True,
        "ExecutablePath": "Contents/MacOS/BlueToolFixup",
        "MaxKernel": "",
        "MinKernel": "",
        "PlistPath": "Contents/Info.plist"
    },
    {
        "Arch": "Any",
        "BundlePath": "FeatureUnlock.kext",
        "Comment": "Enable Continuity Features",
        "Enabled": True,
        "ExecutablePath": "Contents/MacOS/FeatureUnlock",
        "MaxKernel": "",
        "MinKernel": "",
        "PlistPath": "Contents/Info.plist"
    }
]

def update_config():
    if not os.path.exists(BACKUP_PATH):
        import shutil
        shutil.copy2(CONFIG_PATH, BACKUP_PATH)
        print(f"Created backup at {BACKUP_PATH}")

    with open(CONFIG_PATH, 'rb') as f:
        plist = plistlib.load(f)

    kernel_add = plist['Kernel']['Add']
    
    # Check if already exists
    current_paths = [k['BundlePath'] for k in kernel_add]
    
    for new_kext in NEW_KEXTS:
        if new_kext['BundlePath'] not in current_paths:
            print(f"Adding {new_kext['BundlePath']}...")
            # Insert BlueToolFixup after Lilu (index 0)
            if new_kext['BundlePath'] == "BlueToolFixup.kext":
                kernel_add.insert(1, new_kext)
            else:
                kernel_add.append(new_kext)
        else:
            print(f"{new_kext['BundlePath']} already in config.plist, ensuring it's enabled.")
            for k in kernel_add:
                if k['BundlePath'] == new_kext['BundlePath']:
                    k['Enabled'] = True

    with open(CONFIG_PATH, 'wb') as f:
        plistlib.dump(plist, f)
    print("Successfully updated config.plist")

if __name__ == "__main__":
    update_config()
