import ctypes
import ctypes.util
import Quartz

# Load CoreGraphics
cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreGraphics"))

# Define CGDisplayCreateUUIDFromDisplayID
# CFUUIDRef CGDisplayCreateUUIDFromDisplayID(CGDirectDisplayID display);
cg.CGDisplayCreateUUIDFromDisplayID.restype = ctypes.c_void_p
cg.CGDisplayCreateUUIDFromDisplayID.argtypes = [ctypes.c_uint32]

def get_main_display_uuid():
    display_id = Quartz.CGMainDisplayID()
    uuid_ref = cg.CGDisplayCreateUUIDFromDisplayID(display_id)
    if not uuid_ref:
        return None
    
    # CFStringRef CFUUIDCreateString(CFAllocatorRef alloc, CFUUIDRef uuid);
    # Since we have PyObjC CFUUIDCreateString might be available
    uuid_str = Quartz.CFUUIDCreateString(None, uuid_ref)
    return str(uuid_str)

if __name__ == "__main__":
    uuid = get_main_display_uuid()
    print(f"Main Display UUID: {uuid}")
