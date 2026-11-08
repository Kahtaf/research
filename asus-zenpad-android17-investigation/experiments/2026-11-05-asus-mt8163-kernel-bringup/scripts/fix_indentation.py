#!/usr/bin/env python3
from source_edits import replace
replace('sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_dl1_bt.c','\t\tPRINTK_AUDDRV("mtkalsa_playback_constraints\\n");','\tPRINTK_AUDDRV("mtkalsa_playback_constraints\\n");')
replace('drivers/misc/mediatek/base/power/mt8163/mt_cpufreq.c','\t\tcpufreq_ver("num_online_cpus = %d, cur_khz = %d\\n",\n\t\t\tnum_online_cpus(),\n\t\t\tcur_khz);','\tcpufreq_ver("num_online_cpus = %d, cur_khz = %d\\n",\n\t\tnum_online_cpus(),\n\t\tcur_khz);')
