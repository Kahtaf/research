#!/usr/bin/env python3
from source_edits import replace
replace('sound/soc/codecs/rt551x.c','extern int set_dynamic_boost(int duration, int prio_mode);','#if IS_ENABLED(CONFIG_MTK_DYNAMIC_BOOST)\nextern int set_dynamic_boost(int duration, int prio_mode);\n#endif')
replace('sound/soc/codecs/rt551x.c','\tset_dynamic_boost(200, PRIO_TWO_BIGS_TWO_LITTLES_MAX_FREQ);','#if IS_ENABLED(CONFIG_MTK_DYNAMIC_BOOST)\n\tset_dynamic_boost(200, PRIO_TWO_BIGS_TWO_LITTLES_MAX_FREQ);\n#endif')
