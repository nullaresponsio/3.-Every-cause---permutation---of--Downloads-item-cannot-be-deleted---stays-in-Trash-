Below is a high-level “map” of everything involved in deleting a file on modern macOS, from power-on to the Finder UI, followed by a breakdown of every layer’s on-disk origin and a catalogue of every permutation that can block or confuse that deletion.

⸻


                              ┌───────────────┐
                              │   EFI Boot    │ ← Firmware (Boot ROM)
                              └───────────────┘
                                     ↓
                              ┌───────────────┐
                              │  boot.efi     │ ← macOS bootloader
                              └───────────────┘
                                     ↓
                              ┌───────────────┐
                              │   XNU Kernel  │ ← Core (monolithic + Mach)
                              │  • I/O Kit    │   • BSD/VFS layer
                              │  • APFS driver│
                              └───────────────┘
                                     ↓
                              ┌───────────────┐
                              │ launchd (1)   │ ← First user‐space daemon
                              └───────────────┘
                                     ↓
                              ┌───────────────┐
                              │  WindowServer │ ← UI server
                              └───────────────┘
                                     ↓
                              ┌───────────────┐
                              │   Finder.app  │ ← “Trash” UI
                              └───────────────┘


┌──────────────────────┐
│  d e v i c e  l a y e r │
│ ──────────────────── │
│  NVMe Controller      │ ← PCIe commands, TRIM
│  NAND Flash (dies)    │ ← physical pages + blocks
└──────────────────────┘


⸻

1. On-disk origins
	1.	Firmware & bootloader
– Stored in the Mac’s EFI partition (special hidden region, not APFS)
– boot.efi lives in the APFS Preboot volume
	2.	Kernel (XNU)
– /System/Library/Kernels/kernel
– Loaded into protected RAM at early boot
	3.	APFS Container
– Single “container” holds multiple volumes (System, Data, Preboot, Recovery)
– Logical-to-physical mapping of files → extents → SSD pages via the FTL
	4.	User data
– Your Downloads folder lives in your Data volume:

/Users/<you>/Downloads/

– Each file has a catalog record in the APFS metadata B-tree

	5.	Trash
– macOS implements Trash by moving a file via rename(2) into:

~/.Trash/<original name>

– The .Trash directory is itself an APFS directory under your home

	6.	Actual free space
– When you “Empty Trash,” Finder issues unlink(2) on that file
– APFS marks its extents free in its allocation bitmap
– Immediately sends an NVMe TRIM command down to the SSD
– The SSD’s Flash Translation Layer (FTL) will erase pages later during garbage collection

⸻

2. The Finder process memory map

Process: Finder.app
────────────────────────────────────────────
 0x0000_0000    +------------------+  ← code segment (.text)
                |   Finder code    |
                +------------------+
 0x00XX_0000    +------------------+  ← data (.data + .bss)
                | static globals   |
                +------------------+
      …         +------------------+  ← heap (malloc, CFAllocator…)
                | dynamic objects  |
                +------------------+
 0x7FFF_FFFF    +------------------+  ← stack (per thread)
                | locals / frames  |
                +------------------+


⸻

3. Every cause (“permutation”) of “Downloads item cannot be deleted / stays in Trash”
	1.	Open file descriptor
– Any process (Preview, Quick Look, antivirus, Spotlight) still has it open → unlink deferred.
	2.	Immutable or locked flag
– chflags uchg or Finder’s “Locked” checkbox
– Prevents rename/unlink until you chflags nouchg.
	3.	Permissions / ACLs
– You’re not owner, or parent directory lacks write permission
– Extended ACLs can deny delete even if Unix bits allow it.
	4.	Volume read-only
– External USB or disk image mounted RO
– APFS snapshot (local Time Machine snapshot) pins the file.
	5.	System Integrity Protection (SIP)
– Protects certain system paths and files from even root
– If your Downloads is symlinked oddly, SIP might block.
	6.	iCloud-optimised storage
– File resides only in cloud, not local
– Download-in-progress or stuck sync can’t be trashed.
	7.	Spotlight indexing
– mdworker holds a lock while indexing new files.
	8.	Antivirus / security tool
– Real-time scanner intercepts delete.
	9.	APFS corruption
– Catalog B-tree or extent map inconsistent → FS refuses to free.
	10.	Finder UI bug
– Rare race in the UI; works via Terminal.
	11.	Hard link / symlink confusion
– You deleted one link but another path still references same inode.
	12.	SSD-level quirks
– TRIM disabled (external enclosure) → free space not reclaimed
– FTL bug: pages marked free but not yet erased → shows content until GC.
	13.	Extended attributes
– com.apple.quarantine / com.apple.provenance flags
– Sometimes needs xattr -c first.

⸻

Troubleshooting checklist
	1.	lsof | grep /Users/<you>/Downloads/problem.file
	2.	chflags nouchg /path/to/file
	3.	chmod u+w ~/.Trash
	4.	rm -rf ~/.Trash/problem.file (in Terminal)
	5.	diskutil verifyVolume / && diskutil repairVolume /
	6.	Reboot (clears open-FD leaks and refreshes FTL)
	7.	Disable SIP (csrutil disable) if it’s a protected-path quirk
	8.	tmutil listlocalsnapshots / → delete stale snapshots

⸻

By understanding the full path—from EFI firmware through APFS and NVMe to the Finder UI—and enumerating every layer where a lock, flag, or bug can intervene, you can pinpoint exactly why that Downloads item refuses to go away.