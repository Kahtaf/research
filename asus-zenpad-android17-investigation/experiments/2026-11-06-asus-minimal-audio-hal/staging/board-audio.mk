# SPDX-License-Identifier: Apache-2.0
# Must match the compiled primary HAL and installed HIDL implementation ELFs.
SOONG_CONFIG_NAMESPACES += android_hardware_audio
SOONG_CONFIG_android_hardware_audio += run_64bit
SOONG_CONFIG_android_hardware_audio_run_64bit := true
