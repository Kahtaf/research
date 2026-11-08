# SPDX-License-Identifier: Apache-2.0
# Initial module-build target for the observed ASUS P00A_2 / MT8163 unit.
TARGET_NO_BOOTLOADER := true
TARGET_BOARD_PLATFORM := mt8163
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := cortex-a53
TARGET_CPU_ABI := arm64-v8a
TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_VARIANT := cortex-a53
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi

TARGET_MAX_PAGE_SIZE_SUPPORTED := 4096
TARGET_SCREEN_WIDTH := 800
TARGET_SCREEN_HEIGHT := 1280
TARGET_SCREEN_DENSITY := 213

# Live GPT sizes; the firmware ZIP scatter differs and must not define offsets.
BOARD_BOOTIMAGE_PARTITION_SIZE := 16740352
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 16740352
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 3753902080
BOARD_USERDATAIMAGE_PARTITION_SIZE := 11331268096
BOARD_FLASH_BLOCK_SIZE := 512
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_COPY_OUT_VENDOR := system/vendor

TARGET_KERNEL_SOURCE := kernel/asus/p00a
TARGET_KERNEL_CONFIG := asus_p00a_defconfig
BOARD_KERNEL_IMAGE_NAME := Image.gz-dtb

# Export real kernel settings to Lineage's generator. Keep the independently
# verified GCC 13 toolchain for this 4.9 header step; full clang port is pending.
include vendor/lineage/config/BoardConfigKernel.mk
KERNEL_MAKE_CMD := /usr/bin/make
KERNEL_MAKE_FLAGS := HOSTCC=/usr/bin/gcc HOSTCXX=/usr/bin/g++
KERNEL_CROSS_COMPILE := CROSS_COMPILE=/usr/bin/aarch64-linux-gnu-
TOOLS_PATH_OVERRIDE :=
include vendor/lineage/config/BoardConfigSoong.mk
