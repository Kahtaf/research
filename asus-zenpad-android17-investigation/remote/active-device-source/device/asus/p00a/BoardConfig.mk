# SPDX-License-Identifier: Apache-2.0
# Staged full-system target for ASUS P00A_2; not deployed to the active build.
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
TARGET_COPY_OUT_PRODUCT := system/product
TARGET_COPY_OUT_SYSTEM_EXT := system/system_ext

TARGET_KERNEL_SOURCE := kernel/asus/p00a-fd
TARGET_KERNEL_CONFIG := asus_p00a_combined_defconfig
BOARD_KERNEL_IMAGE_NAME := Image.gz-dtb
TARGET_PREBUILT_KERNEL := device/asus/p00a/prebuilt/Image.gz-dtb
TARGET_FORCE_PREBUILT_KERNEL := true

# Export real kernel settings to Lineage's generator. Keep the independently
# verified GCC 13 toolchain for this 4.9 header step; full clang port is pending.
include vendor/lineage/config/BoardConfigKernel.mk
KERNEL_MAKE_CMD := /usr/bin/make
KERNEL_MAKE_FLAGS := HOSTCC=/usr/bin/gcc HOSTCXX=/usr/bin/g++
KERNEL_CROSS_COMPILE := CROSS_COMPILE=/usr/bin/aarch64-linux-gnu-
TOOLS_PATH_OVERRIDE :=
include vendor/lineage/config/BoardConfigSoong.mk

# Exact stock boot header layout; MTK wrappers are added after AOSP packaging.
BOARD_BOOTIMG_HEADER_VERSION := 0
BOARD_KERNEL_BASE := 0x40000000
BOARD_KERNEL_OFFSET := 0x00080000
BOARD_RAMDISK_OFFSET := 0x04000000
BOARD_SECOND_OFFSET := 0x00f00000
BOARD_KERNEL_TAGS_OFFSET := 0x0e000000
BOARD_KERNEL_PAGESIZE := 2048
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2 build_version=3
# Both first-stage fs_mgr and second-stage init must select mt8163 files.
# Header v0 carries these in cmdline, not a vendor_boot bootconfig.
BOARD_KERNEL_CMDLINE += androidboot.hardware=mt8163 androidboot.fstab_suffix=mt8163
BOARD_KERNEL_CMDLINE += androidboot.boot_devices=soc/11230000.mmc
# Android 17 Makefile passes base/pagesize but does not consume these offset
# variables. Pass every measured offset explicitly to mkbootimg.
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOTIMG_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --kernel_offset $(BOARD_KERNEL_OFFSET)
BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)
BOARD_MKBOOTIMG_ARGS += --second_offset $(BOARD_SECOND_OFFSET)
BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_KERNEL_TAGS_OFFSET)
BOARD_RAMDISK_USE_LZ4 := false
BOARD_RAMDISK_USE_XZ := false
BOARD_AVB_ENABLE := false
AB_OTA_UPDATER := false
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
DEVICE_MANIFEST_FILE := device/asus/p00a/manifest.xml
DEVICE_MANIFEST_FILE += device/asus/p00a/firstboot/manifest-keymaster.xml
BOARD_VENDOR_SEPOLICY_DIRS += device/asus/p00a/sepolicy/vendor

include device/asus/p00a/connectivity/BoardConfig-connectivity.mk
BOARD_VENDOR_SEPOLICY_DIRS += device/asus/p00a/radio/sepolicy
DEVICE_MANIFEST_FILE += device/asus/p00a/radio/manifest-bluetooth.xml

include device/asus/p00a/sensors/BoardConfig.mk
