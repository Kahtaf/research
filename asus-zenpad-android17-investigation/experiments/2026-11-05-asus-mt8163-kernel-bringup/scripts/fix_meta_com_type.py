#!/usr/bin/env python3
from source_edits import replace
replace('drivers/misc/mediatek/boot/mtk_boot.c','unsigned int get_meta_com_type(void)','enum meta_com_type get_meta_com_type(void)')
