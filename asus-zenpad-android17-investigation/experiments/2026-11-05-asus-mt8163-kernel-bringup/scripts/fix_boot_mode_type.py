#!/usr/bin/env python3
from source_edits import replace
replace('drivers/misc/mediatek/boot/mtk_boot_common.c','unsigned int get_boot_mode(void)','enum boot_mode_t get_boot_mode(void)')
