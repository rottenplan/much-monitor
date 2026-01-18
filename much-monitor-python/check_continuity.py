import subprocess

def check_continuity():
    print("--- Continuity & Handoff Check ---")
    
    # Check Handoff status via defaults
    try:
        handoff = subprocess.check_output(["defaults", "read", "com.apple.coreservices.useractivityd", "UAContinuityApiEnabled"], stderr=subprocess.STDOUT).decode().strip()
        print(f"Handoff API Enabled: {handoff}")
    except:
        print("Handoff API status: Could not determine (might be default)")

    # Check for multiple Bluetooth Controllers
    try:
        usb_info = subprocess.check_output(["system_profiler", "SPUSBDataType"]).decode()
        controllers = []
        if "Intel Corporation" in usb_info and "Bluetooth" in usb_info:
            controllers.append("Intel Bluetooth")
        if "0x05ac" in usb_info and "Bluetooth" in usb_info:
            controllers.append("Apple/Broadcom Bluetooth")
        
        if len(controllers) > 1:
            print(f"WARNING: Multiple Bluetooth controllers detected: {', '.join(controllers)}")
            print("Action: Disable the Intel Bluetooth in BIOS to avoid conflicts.")
        else:
            print(f"Bluetooth controller detected: {controllers[0] if controllers else 'None'}")
    except Exception as e:
        print(f"Error checking USB: {e}")

    # Check for Continuity Camera support in system
    try:
        # This is a bit hacky but checks if the system thinks it supports it
        # On Ventura+, we can check if the continuity camera service is running? 
        # Actually, let's just check the hardware model again for the user.
        model = subprocess.check_output(["sysctl", "-n", "hw.model"]).decode().strip()
        print(f"Model Identifier: {model}")
    except:
        pass

if __name__ == "__main__":
    check_continuity()
