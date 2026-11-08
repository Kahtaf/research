/* Included at stext before preserve_boot_args. No BL, stack, or mutable globals.
 * Only x4..x17/NZCV are scratch. Boot x0..x3, x18..x30 and SP survive.
 * Bounded structural FDT admission; unrelated chosen contents are ignored.
 */
#include "asus_entry_tag.h"
	.global asus_entry_text_begin
asus_entry_text_begin:
	mrs x4, CurrentEL
	cmp x4, #4
	b.eq .Laet_el1
	cmp x4, #8
	diag_refuse b.ne, , , 12
	mrs x4, sctlr_el2
	b .Laet_sctlr
.Laet_el1:
	mrs x4, sctlr_el1
.Laet_sctlr:
	diag_refuse tbnz, x4, #0, 18
	diag_refuse tbnz, x4, #2, 19
	/* Read only the 40-byte header until totalsize has been admitted. */
	tst x0, #7
	diag_refuse b.ne, , , 22
	mov x4, #0x40000000
	cmp x0, x4
	diag_refuse b.lo, , , 25
	mov x4, #0xbd600000
	sub x4, x4, #40
	cmp x0, x4
	diag_refuse b.hi, , , 29
	ldr w4, [x0]
	rev w4, w4
	movz w5, #0xfeed
	movk w5, #0xd00d, lsl #16
	cmp w4, w5
	diag_refuse b.ne, , , 35
	ldr w5, [x0, #4]
	rev w5, w5
	cmp x5, #40
	diag_refuse b.lo, , , 39
	mov x4, #0x200000       // ARM64 boot FDT ceiling, not expected blob size
	cmp x5, x4
	diag_refuse b.hi, , , 42
	add x6, x0, x5         // u32 length widened before arithmetic
	mov x4, #0xbd600000
	cmp x6, x4
	diag_refuse b.hi, , , 46
	ldr w4, [x0, #20]
	rev w4, w4
	cmp w4, #17
	diag_refuse b.ne, , , 50
	ldr w4, [x0, #24]
	rev w4, w4
	cmp w4, #16
	diag_refuse b.lo, , , 54
	cmp w4, #17
	diag_refuse b.hi, , , 56
	/* Reject physical FDT overlap with console, kernel, or exact initrd. */
	mov x4, #0x44480000
	cmp x0, x4
	b.hs .Laet_fdt_kernel
	mov x4, #0x44400000
	cmp x6, x4
	diag_refuse b.hi, , , 63
.Laet_fdt_kernel:
	adr_l x4, _end
	cmp x0, x4
	b.hs .Laet_fdt_initrd
	adr_l x4, _text
	cmp x6, x4
	diag_refuse b.hi, , , 70
.Laet_fdt_initrd:
	movz x4, #0xf007
	movk x4, #0x4403, lsl #16
	cmp x0, x4
	b.hs .Laet_kernel_console
	mov x4, #0x44000000
	cmp x6, x4
	diag_refuse b.hi, , , 78
.Laet_kernel_console:
	adr_l x4, _text
	mov x7, #0x44480000
	cmp x4, x7
	b.hs .Laet_parse
	adr_l x4, _end
	mov x7, #0x44400000
	cmp x4, x7
	diag_refuse b.hi, , , 87

.Laet_parse:
	/* The complete linked kernel must also lie in the admitted RAM bank. */
	adr_l x4, _text
	mov x7, #0x40000000
	cmp x4, x7
	diag_refuse b.lo, , , 94
	adr_l x7, _end
	cmp x7, x4
	diag_refuse b.ls, , , 97
	mov x4, #0xbd600000
	cmp x7, x4
	diag_refuse b.hi, , , 100
	/* Preserve the pinned reporter load range independently of /chosen. */
	adr_l x4, _text
	movz x12, #0xf007
	movk x12, #0x4403, lsl #16
	cmp x4, x12
	b.hs .Laet_kernel_initrd_clear
	mov x12, #0x44000000
	cmp x7, x12
	diag_refuse b.hi, , , 109
.Laet_kernel_initrd_clear:
	/* Header offsets/sizes are u32; all sums below use x registers. */
	ldr w4, [x0, #8]
	rev w4, w4
	ldr w8, [x0, #36]
	rev w8, w8
	cmp x4, #40
	diag_refuse b.lo, , , 117
	tst x4, #3
	diag_refuse b.ne, , , 119
	tst x8, #3
	diag_refuse b.ne, , , 121
	cmp x8, #16
	diag_refuse b.lo, , , 123
	add x8, x4, x8
	cmp x8, x5
	diag_refuse b.hi, , , 126
	ldr w6, [x0, #12]
	rev w6, w6
	ldr w7, [x0, #32]
	rev w7, w7
	cmp x6, #40
	diag_refuse b.lo, , , 132
	diag_refuse cbz, x7, , 133
	add x7, x6, x7
	cmp x7, x5
	diag_refuse b.hi, , , 136
	cmp x4, x7
	b.hs .Laet_blocks_separate
	cmp x6, x8
	diag_refuse b.lo, , , 140
.Laet_blocks_separate:
	/* Memreserve ends at its bounded zero pair, before either data block.
	 * It may be placed after either block as well. No alias of the writer.
	 */
	ldr w9, [x0, #16]
	rev w9, w9
	cmp x9, #40
	diag_refuse b.lo, , , 148
	tst x9, #7
	diag_refuse b.ne, , , 150
.Laet_reserve_loop:
	add x10, x9, #16
	cmp x10, x5
	diag_refuse b.hi, , , 154
	cmp x9, x8
	b.hs .Laet_mr_strings
	cmp x10, x4
	diag_refuse b.hi, , , 158
.Laet_mr_strings:
	cmp x9, x7
	b.hs .Laet_mr_load
	cmp x10, x6
	diag_refuse b.hi, , , 163
.Laet_mr_load:
	add x11, x0, x9
	ldr x12, [x11]
	ldr x13, [x11, #8]
	rev x12, x12
	rev x13, x13
	orr x14, x12, x13
	cbz x14, .Laet_mr_end
	adds x13, x12, x13
	diag_refuse b.cs, , , 173
	cmp x13, x12
	diag_refuse b.eq, , , 175       // nonzero-address, zero-size entry is ambiguous
	mov x14, #0x44480000
	cmp x12, x14
	b.hs .Laet_mr_next
	mov x14, #0x44400000
	cmp x13, x14
	diag_refuse b.hi, , , 181
.Laet_mr_next:
	mov x9, x10
	b .Laet_reserve_loop
.Laet_mr_end:
	add x4, x0, x4         // cursor
	add x5, x0, x8         // structure end
	add x6, x0, x6         // strings start
	add x7, x0, x7         // strings end
	mov x8, #0            // depth, capped at 32
	mov x9, #0            // low 2 bits: root-child kind; bits depth+2: children seen
	/* Global bits: 0 root seen, 1 root closed, 2 compatible, 3/4 root
	 * cells, 5 memory seen, 6 memory reg, 7 reserved seen, 8/9 reserved
	 * cells, 10 ranges, 11 unique retained intersection; 14 per-child
	 * device_type, 15 memory type, 16 compatible match, 17 usable-memory.
	 * Child flags: 0 reg, 1 compatible seen, 2 compatible correct,
	 * 3 no-map, 4 reusable, 5 status seen, 6 status good, 7 intersection.
	 */
	mov x10, #0           // global critical seen/satisfied bits
	mov x11, #0           // reserved start offset (high32), current child flags (low32)

	/* Exact bounded string compare: x14 points to already bounded bytes,
	 * x15 is their length. Scratch x12,x13,x16,x17 only. Literals are tiny,
	 * position-independent rodata, never a signature search in the blob.
	 */
	.macro aet_eq literal, length, fail
	cmp x15, #\length
	b.ne \fail
	adr_l x16, .Laet_string\@
	mov x17, #0
.Laet_eq_loop\@:
	ldrb w12, [x14, x17]
	ldrb w13, [x16, x17]
	cmp w12, w13
	b.ne \fail
	add x17, x17, #1
	cmp x17, #\length
	b.lo .Laet_eq_loop\@
	.pushsection .init.rodata,"a"
.Laet_string\@:
	.ascii "\literal"
	.popsection
	.endm
	/* Structure values are only 4-byte aligned; use u32 loads even for u64
	 * reg cells, so SCTLR.A need not be changed or assumed clear. */
	.macro aet_be64 dst, base, offset, tmp
	ldr w\dst, [\base, #\offset]
	rev w\dst, w\dst
	ldr w\tmp, [\base, #(\offset + 4)]
	rev w\tmp, w\tmp
	orr x\dst, x\tmp, x\dst, lsl #32
	.endm
	.macro aet_seen bit
	diag_refuse tbnz, x10, #\bit, 234
	orr x10, x10, #(1 << \bit)
	.endm
	.macro aet_child_seen bit
	diag_refuse tbnz, x11, #\bit, 238
	orr x11, x11, #(1 << \bit)
	.endm
	.macro aet_len length
	ldur w12, [x4, #-8]
	rev w12, w12
	cmp x12, #\length
	diag_refuse b.ne, , , 245
	.endm
.Laet_token:
	add x12, x4, #4
	cmp x12, x5
	diag_refuse b.hi, , , 250
	ldr w12, [x4], #4
	rev w12, w12
	cmp w12, #1
	b.eq .Laet_begin
	cmp w12, #2
	b.eq .Laet_end_node
	cmp w12, #3
	b.eq .Laet_prop
	cmp w12, #4
	b.eq .Laet_token
	cmp w12, #9
	diag_refuse b.ne, , , 262
	diag_refuse cbnz, x8, , 263
	cmp x4, x5
	diag_refuse b.ne, , , 265
	mov x12, #0x8fff       // all required globals, including memory device_type
	and x13, x10, x12
	cmp x13, x12
	diag_refuse b.ne, , , 269
	b .Laet_oem
.Laet_begin:
	cmp x8, #32
	diag_refuse b.hs, , , 273
	add x12, x8, #2
	mov x13, #1
	lsl x13, x13, x12
	orr x9, x9, x13        // parent has children: no more properties
	add x8, x8, #1
	mov x14, x4
.Laet_node_name:
	cmp x4, x5
	diag_refuse b.hs, , , 282
	ldrb w12, [x4], #1
	cmp w12, #47          // '/' cannot manufacture a path
	diag_refuse b.eq, , , 285
	cbnz w12, .Laet_node_name
	sub x15, x4, x14
	sub x15, x15, #1
	add x4, x4, #3
	and x4, x4, #0xfffffffffffffffc
	cmp x4, x5
	diag_refuse b.hi, , , 292
	cmp x8, #1
	b.ne .Laet_nonroot
	diag_refuse cbnz, x15, , 295
	aet_seen 0
	b .Laet_token
.Laet_nonroot:
	diag_refuse cbz, x15, , 299
	cmp x8, #2
	b.ne .Laet_deep_node
	and x9, x9, #0xfffffffffffffffc
	aet_eq "reserved-memory", 15, .Laet_try_memory
	aet_seen 7
	orr x9, x9, #2
	sub x11, x4, x0
	lsl x11, x11, #32
	b .Laet_token
.Laet_try_memory:
	/* memory and memory@unit-address are the only admitted memory nodes. */
	cmp x15, #6
	b.lo .Laet_token
	ldrb w12, [x14, #6]    // bounded NUL is present for exact "memory"
	cbz w12, .Laet_memory_name
	cmp w12, #64
	b.ne .Laet_token
	cmp x15, #7
	diag_refuse b.ls, , , 318
.Laet_memory_name:
	mov x15, #6
	aet_eq "memory", 6, .Laet_token
	aet_seen 5
	orr x9, x9, #1
	b .Laet_token
.Laet_deep_node:
	and x12, x9, #3
	cmp x12, #1
	diag_refuse b.eq, , , 328        // no nested memory interpretation
	cmp x12, #2
	b.ne .Laet_token
	cmp x8, #3
	diag_refuse b.ne, , , 332        // no nested reservation ambiguity
	and x11, x11, #0xffffffff00000000
	/* Reject duplicate reservation child names. Rescan only the already
	 * validated prefix of this reserved-memory node, using no saved stack.
	 */
	lsr x12, x11, #32
	add x12, x0, x12
	mov x13, #2
.Laet_unique:
	sub x16, x14, #4
	cmp x12, x16
	b.eq .Laet_token
	ldr w16, [x12], #4
	rev w16, w16
	cmp w16, #1
	b.eq .Laet_unique_name
	cmp w16, #2
	b.eq .Laet_unique_end
	cmp w16, #3
	b.ne .Laet_unique
	ldr w16, [x12]
	rev w16, w16
	add x12, x12, #8
	add x12, x12, x16
	add x12, x12, #3
	and x12, x12, #0xfffffffffffffffc
	b .Laet_unique
.Laet_unique_end:
	sub x13, x13, #1
	b .Laet_unique
.Laet_unique_name:
	add x13, x13, #1
	cmp x13, #3
	b.ne .Laet_unique_skip
	mov x16, #0
.Laet_unique_cmp:
	ldrb w15, [x14, x16]
	ldrb w17, [x12, x16]
	cmp w15, w17
	b.ne .Laet_unique_skip
	diag_refuse cbz, w15, , 372
	add x16, x16, #1
	b .Laet_unique_cmp
.Laet_unique_skip:
	ldrb w16, [x12], #1
	cbnz w16, .Laet_unique_skip
	add x12, x12, #3
	and x12, x12, #0xfffffffffffffffc
	b .Laet_unique
.Laet_end_node:
	diag_refuse cbz, x8, , 382
	cmp x8, #3
	b.ne .Laet_end_shallow
	and x12, x9, #3
	cmp x12, #2
	b.ne .Laet_end_shallow
	tbz x11, #7, .Laet_end_shallow
	/* intersecting child: reg + compatible must be present and correct;
	 * no-map/reusable absent, status absent or explicitly okay/ok.
	 */
	and x12, x11, #0x1f
	cmp x12, #7
	diag_refuse b.ne, , , 394
	tbz x11, #5, .Laet_reservation_ok
	diag_refuse tbz, x11, #6, 396
.Laet_reservation_ok:
	aet_seen 11
.Laet_end_shallow:
	cmp x8, #1
	b.ne .Laet_end_clear
	aet_seen 1
.Laet_end_clear:
	add x12, x8, #2
	mov x13, #1
	lsl x13, x13, x12
	bic x9, x9, x13
	cmp x8, #2
	b.ne .Laet_depth_down
	and x9, x9, #0xfffffffffffffffc
	bic x10, x10, #0x4000 // per-root-child device_type duplicate bit
.Laet_depth_down:
	sub x8, x8, #1
	b .Laet_token
.Laet_prop:
	diag_refuse cbz, x8, , 416
	add x12, x8, #2
	mov x13, #1
	lsl x13, x13, x12
	tst x9, x13
	diag_refuse b.ne, , , 421        // properties must precede child nodes
	add x12, x4, #8
	cmp x12, x5
	diag_refuse b.hi, , , 424
	ldr w12, [x4]
	rev w12, w12
	ldr w14, [x4, #4]
	rev w14, w14
	add x4, x4, #8        // property value; length remains at cursor-8
	add x13, x4, x12
	add x13, x13, #3
	and x13, x13, #0xfffffffffffffffc
	cmp x13, x5
	diag_refuse b.hi, , , 434
	sub x12, x7, x6
	cmp x14, x12
	diag_refuse b.hs, , , 437
	add x14, x6, x14
	mov x15, x14
.Laet_prop_name:
	cmp x15, x7
	diag_refuse b.hs, , , 442
	ldrb w12, [x15], #1
	cbnz w12, .Laet_prop_name
	sub x15, x15, x14
	sub x15, x15, #1
	diag_refuse cbz, x15, , 447
	aet_eq "device_type", 11, .Laet_not_device_type
	cmp x8, #2
	b.ne .Laet_type_value
	aet_seen 14
.Laet_type_value:
	ldur w15, [x4, #-8]
	rev w15, w15
	cmp x15, #6
	b.lo .Laet_other_type
	mov x15, #6
	mov x14, x4
	aet_eq "memory", 6, .Laet_other_type
	ldur w12, [x4, #-8]
	rev w12, w12
	cmp x12, #6
	diag_refuse b.eq, , , 463        // do not borrow a NUL from alignment padding
	ldrb w12, [x4, #6]
	cbnz w12, .Laet_other_type
	aet_len 7              // reject memory\0 plus hidden trailing bytes
	cmp x8, #2
	diag_refuse b.ne, , , 468
	and x12, x9, #3
	cmp x12, #1
	diag_refuse b.ne, , , 471
	aet_seen 15
	b .Laet_prop_next
.Laet_other_type:
	cmp x8, #2
	b.ne .Laet_prop_next
	and x12, x9, #3
	cmp x12, #1
	diag_refuse b.eq, , , 479
	b .Laet_prop_next
.Laet_not_device_type:
	cmp x8, #1
	b.eq .Laet_root_prop
	cmp x8, #2
	b.ne .Laet_child_prop
	and x12, x9, #3
	cmp x12, #1
	b.eq .Laet_memory_prop
	cmp x12, #2
	b.eq .Laet_reserved_prop
	b .Laet_prop_next
.Laet_root_prop:
	aet_eq "compatible", 10, .Laet_root_cells
	aet_seen 2
	/* A bounded list of nonempty NUL-terminated strings, not a substring. */
	mov x14, x4
	mov x16, #0           // match recorded in global bit16
.Laet_compat_item:
	ldur w13, [x4, #-8]
	rev w13, w13
	add x13, x4, x13
	cmp x14, x13
	diag_refuse b.hs, , , 503
	mov x15, x14
.Laet_compat_nul:
	cmp x15, x13
	diag_refuse b.hs, , , 507
	ldrb w12, [x15], #1
	cbnz w12, .Laet_compat_nul
	sub x15, x15, x14
	sub x15, x15, #1
	diag_refuse cbz, x15, , 512
	aet_eq "asus,p00a", 9, .Laet_compat_advance
	orr x10, x10, #0x10000
.Laet_compat_advance:
	add x14, x14, x15
	add x14, x14, #1
	ldur w13, [x4, #-8]
	rev w13, w13
	add x13, x4, x13
	cmp x14, x13
	b.lo .Laet_compat_item
	diag_refuse tbz, x10, #16, 523
	b .Laet_prop_next
.Laet_root_cells:
	aet_eq "#address-cells", 14, .Laet_root_size
	aet_seen 3
	b .Laet_two_cells
.Laet_root_size:
	aet_eq "#size-cells", 11, .Laet_prop_next
	aet_seen 4
	b .Laet_two_cells
.Laet_reserved_prop:
	aet_eq "#address-cells", 14, .Laet_reserved_size
	aet_seen 8
	b .Laet_two_cells
.Laet_reserved_size:
	aet_eq "#size-cells", 11, .Laet_reserved_ranges
	aet_seen 9
	b .Laet_two_cells
.Laet_reserved_ranges:
	aet_eq "ranges", 6, .Laet_prop_next
	aet_seen 10
	aet_len 0
	b .Laet_prop_next
.Laet_two_cells:
	aet_len 4
	ldr w12, [x4]
	rev w12, w12
	cmp w12, #2
	diag_refuse b.ne, , , 551
	b .Laet_prop_next
.Laet_memory_prop:
	aet_eq "reg", 3, .Laet_memory_usable
	aet_seen 6
	b .Laet_memory_cells
.Laet_memory_usable:
	aet_eq "linux,usable-memory", 19, .Laet_prop_next
	aet_seen 17
.Laet_memory_cells:
	aet_len 16
	aet_be64 12, x4, 0, 16
	aet_be64 13, x4, 8, 16
	mov x16, #0x40000000
	cmp x12, x16
	diag_refuse b.ne, , , 566
	mov x16, #0x7d600000
	cmp x13, x16
	diag_refuse b.ne, , , 569
	b .Laet_prop_next
.Laet_child_prop:
	cmp x8, #3
	b.ne .Laet_prop_next
	and x12, x9, #3
	cmp x12, #2
	b.ne .Laet_prop_next
	aet_eq "reg", 3, .Laet_child_compat
	aet_child_seen 0
	ldur w13, [x4, #-8]
	rev w13, w13
	diag_refuse cbz, x13, , 581
	tst x13, #15
	diag_refuse b.ne, , , 583
	add x13, x4, x13
	mov x14, x4
.Laet_reg_loop:
	aet_be64 12, x14, 0, 17
	aet_be64 15, x14, 8, 17
	adds x16, x12, x15
	diag_refuse b.cs, , , 590
	cbz x15, .Laet_reg_next
	mov x17, #0x44480000
	cmp x12, x17
	b.hs .Laet_reg_next
	mov x17, #0x44400000
	cmp x16, x17
	b.ls .Laet_reg_next
	diag_refuse tbnz, x11, #7, 598
	orr x11, x11, #0x80
	cmp x12, x17
	diag_refuse b.ne, , , 601
	mov x17, #0x80000
	cmp x15, x17
	diag_refuse b.ne, , , 604
	/* The retained reservation has exactly one tuple. */
	aet_len 16
.Laet_reg_next:
	add x14, x14, #16
	cmp x14, x13
	b.lo .Laet_reg_loop
	b .Laet_prop_next
.Laet_child_compat:
	aet_eq "compatible", 10, .Laet_child_nomap
	aet_child_seen 1
	mov x14, x4
	ldur w15, [x4, #-8]
	rev w15, w15
	aet_eq "mediatek,ram_console\0", 21, .Laet_prop_next
	orr x11, x11, #4
	b .Laet_prop_next
.Laet_child_nomap:
	aet_eq "no-map", 6, .Laet_child_reusable
	aet_child_seen 3
	b .Laet_prop_next
.Laet_child_reusable:
	aet_eq "reusable", 8, .Laet_child_status
	aet_child_seen 4
	b .Laet_prop_next
.Laet_child_status:
	aet_eq "status", 6, .Laet_prop_next
	aet_child_seen 5
	mov x14, x4
	ldur w15, [x4, #-8]
	rev w15, w15
	aet_eq "ok\0", 3, .Laet_status_okay
	b .Laet_status_good
.Laet_status_okay:
	aet_eq "okay\0", 5, .Laet_prop_next
.Laet_status_good:
	orr x11, x11, #0x40
.Laet_prop_next:
	ldur w12, [x4, #-8]
	rev w12, w12
	add x4, x4, x12
	add x4, x4, #3
	and x4, x4, #0xfffffffffffffffc
	b .Laet_token
	.purgem aet_be64
	.purgem aet_eq
	.purgem aet_seen
	.purgem aet_child_seen
	.purgem aet_len
.Laet_oem:
	/* Read-only OEM geometry admission before the first retained store. */
	mov x4, #0x44400000
	ldr w5, [x4]
	movz w6, #0x4244
	movk w6, #0x4347, lsl #16
	cmp w5, w6
	diag_refuse b.ne, , , 660
	ldr w7, [x4, #4]       // off_pl
	ldr w8, [x4, #8]       // off_lpl
	ldr w9, [x4, #12]      // sz_pl
	cbz x9, .Laet_pl_zero
	cmp x7, #64
	diag_refuse b.lo, , , 666
.Laet_pl_zero:
	add x9, x9, #63
	and x9, x9, #0xffffffffffffffc0
	add x6, x7, x9
	cmp x6, x8
	diag_refuse b.ne, , , 672
	add x8, x8, x9         // end of both PL payloads, 64-bit arithmetic
	mov x5, #0x80000
	cmp x8, x5
	diag_refuse b.hi, , , 676
	ldr w10, [x4, #16]     // off_lk
	ldr w11, [x4, #20]     // off_llk
	ldr w12, [x4, #24]     // sz_lk
	cbz x12, .Laet_lk_zero
	cmp x10, #64
	diag_refuse b.lo, , , 682
	cmp x10, x8            // require separate complete PL/LK regions
	diag_refuse b.lo, , , 684
.Laet_lk_zero:
	add x13, x12, #63
	and x13, x13, #0xffffffffffffffc0
	add x6, x10, x13
	cmp x6, x11
	diag_refuse b.ne, , , 690
	add x11, x11, x13      // end of both LK payloads
	cmp x11, x5
	diag_refuse b.hi, , , 693
	mov x14, #0x200
	cbz x12, .Laet_linux
	mov x14, x11
.Laet_linux:
	cmp x14, #0x40
	diag_refuse b.lo, , , 699
	cmp x8, x14
	diag_refuse b.hi, , , 701
	cmp x11, x14
	diag_refuse b.hi, , , 703
	add x15, x14, #0x400   // exact OEM Linux reason area size
	cmp x15, x5
	diag_refuse b.hs, , , 706
	sub x16, x5, x15       // complete console capacity
	mov x17, #ASUS_ENTRY_TAG_LEN
	cmp x16, x17
	diag_refuse b.lo, , , 710
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
	mov x5, #0xffff
	b diag_finish
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
	.popsection
