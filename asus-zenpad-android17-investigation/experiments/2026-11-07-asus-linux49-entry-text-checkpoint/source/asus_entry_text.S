/* Included at stext before preserve_boot_args. No BL, stack, or mutable globals.
 * Only x4..x17/NZCV are scratch. Boot x0..x3, x18..x30 and SP survive.
 * The exact full runtime FDT is an intentionally strict admission guard:
 * bootloader changes, including harmless ones, refuse without retained writes.
 */
#include "asus_entry_tag.h"
	.global asus_entry_text_begin
asus_entry_text_begin:
	mrs x4, CurrentEL
	cmp x4, #4
	b.eq .Laet_el1
	cmp x4, #8
	b.ne .Laet_done
	mrs x4, sctlr_el2
	b .Laet_sctlr
.Laet_el1:
	mrs x4, sctlr_el1
.Laet_sctlr:
	tbnz x4, #0, .Laet_done
	tbnz x4, #2, .Laet_done
	/* FDT reads are bounded by the exact compiled memory bank. */
	tst x0, #7
	b.ne .Laet_done
	mov x4, #0x40000000
	cmp x0, x4
	b.lo .Laet_done
	mov x5, #ASUS_ENTRY_DTB_LEN
	adds x6, x0, x5
	b.cs .Laet_done
	mov x4, #0xbd600000
	cmp x6, x4
	b.hi .Laet_done
	/* Reject physical FDT overlap with console, kernel, or exact initrd. */
	mov x4, #0x44480000
	cmp x0, x4
	b.hs .Laet_fdt_kernel
	mov x4, #0x44400000
	cmp x6, x4
	b.hi .Laet_done
.Laet_fdt_kernel:
	adr_l x4, _end
	cmp x0, x4
	b.hs .Laet_fdt_initrd
	adr_l x4, _text
	cmp x6, x4
	b.hi .Laet_done
.Laet_fdt_initrd:
	movz x4, #0xf007
	movk x4, #0x4403, lsl #16
	cmp x0, x4
	b.hs .Laet_kernel_console
	mov x4, #0x44000000
	cmp x6, x4
	b.hi .Laet_done
.Laet_kernel_console:
	adr_l x4, _text
	mov x7, #0x44480000
	cmp x4, x7
	b.hs .Laet_compare
	adr_l x4, _end
	mov x7, #0x44400000
	cmp x4, x7
	b.hi .Laet_done
.Laet_compare:
	/* Equality includes header/length, memreserve map, root compatible,
	 * every reservation, memory bank, chosen initrd and boot arguments.
	 * Never trust a runtime offset/length to bound this byte comparison.
	 */
	adr_l x4, asus_entry_expected_dtb
	mov x6, x0
.Laet_dtb_loop:
	ldrb w7, [x4], #1
	ldrb w8, [x6], #1
	cmp w7, w8
	b.ne .Laet_done
	subs x5, x5, #1
	b.ne .Laet_dtb_loop
	/* Read-only OEM geometry admission before the first retained store. */
	mov x4, #0x44400000
	ldr w5, [x4]
	movz w6, #0x4244
	movk w6, #0x4347, lsl #16
	cmp w5, w6
	b.ne .Laet_done
	ldr w7, [x4, #4]       // off_pl
	ldr w8, [x4, #8]       // off_lpl
	ldr w9, [x4, #12]      // sz_pl
	cbz x9, .Laet_pl_zero
	cmp x7, #64
	b.lo .Laet_done
.Laet_pl_zero:
	add x9, x9, #63
	and x9, x9, #0xffffffffffffffc0
	add x6, x7, x9
	cmp x6, x8
	b.ne .Laet_done
	add x8, x8, x9         // end of both PL payloads, 64-bit arithmetic
	mov x5, #0x80000
	cmp x8, x5
	b.hi .Laet_done
	ldr w10, [x4, #16]     // off_lk
	ldr w11, [x4, #20]     // off_llk
	ldr w12, [x4, #24]     // sz_lk
	cbz x12, .Laet_lk_zero
	cmp x10, #64
	b.lo .Laet_done
	cmp x10, x8            // require separate complete PL/LK regions
	b.lo .Laet_done
.Laet_lk_zero:
	add x13, x12, #63
	and x13, x13, #0xffffffffffffffc0
	add x6, x10, x13
	cmp x6, x11
	b.ne .Laet_done
	add x11, x11, x13      // end of both LK payloads
	cmp x11, x5
	b.hi .Laet_done
	mov x14, #0x200
	cbz x12, .Laet_linux
	mov x14, x11
.Laet_linux:
	cmp x14, #0x200
	b.lo .Laet_done
	cmp x8, x14
	b.hi .Laet_done
	cmp x11, x14
	b.hi .Laet_done
	add x15, x14, #0x400   // exact OEM Linux reason area size
	cmp x15, x5
	b.hs .Laet_done
	sub x16, x5, x15       // complete console capacity
	mov x17, #ASUS_ENTRY_TAG_LEN
	cmp x16, x17
	b.lo .Laet_done
	/* MMU and D-cache are off at the admitted EL. These physical stores
	 * do not allocate dirty cache lines. No cache-enable or alias changes.
	 * First invalidate old Linux ring counters, preserving platform bytes.
	 */
	str wzr, [x4, #0x34]
	dsb sy
	str wzr, [x4, #0x38]
	dsb sy
	adr_l x6, asus_entry_tag
	add x7, x4, x15
.Laet_text_loop:
	ldrb w8, [x6], #1
	strb w8, [x7], #1
	subs x17, x17, #1
	b.ne .Laet_text_loop
	dsb sy                   // payload completes before layout/size publication
	str w5, [x4, #0x28]
	str w14, [x4, #0x2c]
	str w15, [x4, #0x30]
	str w16, [x4, #0x3c]
	dsb sy
	mov w17, #ASUS_ENTRY_TAG_LEN
	.global asus_entry_text_commit
asus_entry_text_commit:
	str w17, [x4, #0x38]     // sole nonzero commit, incoming stock-reader ABI
	dsb sy
.Laet_done:
	.global asus_entry_text_end
asus_entry_text_end:
	/* Fall through to the original preserve_boot_args/el2_setup path. */

	.pushsection .init.rodata,"a"
	.balign 8
	.global asus_entry_tag
asus_entry_tag:
	.ascii ASUS_ENTRY_TAG
	.global asus_entry_tag_end
asus_entry_tag_end:
	.balign 8
	.global asus_entry_expected_dtb
asus_entry_expected_dtb:
#include "asus_entry_expected.inc"
	.global asus_entry_expected_dtb_end
asus_entry_expected_dtb_end:
	.popsection
