#@author     
#@category   
#@keybinding 
#@menupath  
#@toolbar    

mapping = {
    "EFI Boot":                    "BOOTFIRMWARE",
    "boot.efi":                    "BOOTLOADER",
    "XNU Kernel":                  "KERNEL",
    "I/O Kit":                     "KERNEL_IOKIT",
    "BSD/VFS":                     "KERNEL_VFS",
    "APFS driver":                 "FILESYSTEM_APFS",
    "launchd":                     "USER_INIT",
    "WindowServer":                "USER_UI",
    "Finder.app":                  "USER_UI_FINDER",
    "NVMe Controller":             "DEVICE_NVME",
    "NAND Flash":                  "DEVICE_NAND",
    "~/Downloads":                 "USER_DATA",
    "~/.Trash":                    "USER_TRASH",
    "Free Space":                  "FREE_SPACE",
}

for place, tag in mapping.items():
    print(f"{place}\t{tag}")