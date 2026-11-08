#!/usr/bin/env python3
from source_edits import replace
replace('drivers/misc/mediatek/video/mt8163/videox/debug.h','#include "ddp_ovl.h"','#include "ddp_ovl.h"\n#include "disp_assert_layer.h"')
replace('drivers/misc/mediatek/video/mt8163/videox/debug.h','extern int DAL_Clean(void);\nextern int DAL_Printf(const char *fmt, ...);\n','')
