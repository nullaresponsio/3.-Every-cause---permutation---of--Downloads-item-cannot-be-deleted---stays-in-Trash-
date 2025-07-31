#!/usr/bin/env python3
"""
mapping.py – generate a radare2 script that scans a Mach‑O for
• the original high‑level boot‑to‑UI landmarks, _and_
• low‑level signatures that correspond to each practical reason
  a file might refuse to leave the Trash.

Invoke directly to print the script to stdout:

    python3 mapping.py  > /tmp/trash_scan.r2
    r2 -q -i /tmp/trash_scan.r2  /path/to/binary
"""

# ────────────────────────────────────────────────────────────
# 1.  ORIGINAL LANDMARKS  (unchanged)
# ────────────────────────────────────────────────────────────
BASE_MAPPING = {
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

# ────────────────────────────────────────────────────────────
# 2.  NEW  –  SIGNATURES FOR EVERY “TRASH‑STUCK” PERMUTATION
#     Each tag’s list is searched both in the raw bytes (/)
#     and in the import/symbol tables (ii~/is~) where relevant.
# ────────────────────────────────────────────────────────────
CAUSE_SIGNATURES = {
    # 1  Open FD / file busy
    "OPENFD": [
        "O_EVTONLY", "kqueue(", "kevent(", "flock(", "F_WRLCK",
        "F_NOCACHE", "fhgfs",
    ],
    # 2  Immutable / append flags
    "IMMUTABLE": [
        "UF_IMMUTABLE", "SF_IMMUTABLE", "UF_APPEND", "SF_APPEND",
        "chflags(", "fchflags(",
    ],
    # 3  Permissions / ACL issues
    "PERMS": [
        "chmod(", "fchmod(", "acl_set_file(", "acl_set_fd(",
        "chmodExtended", "setattrlist(",
    ],
    # 4  Read‑only volume or snapshot pinning
    "READONLY_VOL": [
        "mnt_rdonly", "MP_SNAPSHOT", "APFS_SNAPSHOT", "fs_snapshot_",
    ],
    # 5  System‑Integrity‑Protection path blocking
    "SIP": [
        "csr_check", "com.apple.rootless", "get_entitlement_value",
    ],
    # 6  iCloud / CloudDocs sync
    "ICLOUD": [
        "CloudDocs", "com.apple.CloudDocs", "NSMetadataQuery",
        "com.apple.deferred-delete",
    ],
    # 7  Spotlight / indexing lock
    "SPOTLIGHT": [
        "mdworker", "kMDItemFSName", "FSEvents", "FSEventStream",
    ],
    # 8  Antivirus / endpoint security filter
    "AV": [
        "ScanEngine", "EndpointSecurity", "es_client", "XProtect",
        "VirusTotal",
    ],
    # 9  Low‑level APFS corruption
    "FS_CORRUPT": [
        "BTREE_CORRUPT", "invalid extent", "fsroot tree",
        "container superblock",
    ],
    # 10 Finder / UI‑side failures
    "FINDER_BUG": [
        "com.apple.Finder", "FMErrorDomain", "TrashOperationFailed",
        "FMDuplicate", ".TrashInfo",
    ],
}

# ────────────────────────────────────────────────────────────
# 3.  Helpers
# ────────────────────────────────────────────────────────────
def emit_search_cmd(token: str) -> list[str]:
    """
    Convert a token into one or more r2 search commands.

    If it looks like a function/symbol (has '(' or is C‑identifier‑ish),
    we grep the import table (ii~) and the symbol table (is~).
    Otherwise we treat it as a raw string literal ("/ ").
    """
    if "(" in token or token.isidentifier():
        return [f"ii~{token}", f"is~{token}"]
    return [f"/ {token}"]

# ────────────────────────────────────────────────────────────
# 4.  Main – print the r2 script to stdout
# ────────────────────────────────────────────────────────────
def main() -> None:
    # Original landmark strings
    for place, tag in BASE_MAPPING.items():
        print(f"/ {place}\t# {tag}")

    print("")              # empty line separator
    print("# ---- Failure‑cause signatures ----")

    # New signatures
    for tag, tokens in CAUSE_SIGNATURES.items():
        for t in tokens:
            for cmd in emit_search_cmd(t):
                print(f"{cmd}\t# {tag}")

if __name__ == "__main__":
    main()
