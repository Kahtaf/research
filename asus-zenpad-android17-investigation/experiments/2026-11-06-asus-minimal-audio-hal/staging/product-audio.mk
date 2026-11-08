# SPDX-License-Identifier: Apache-2.0
# FUTURE INPUT ONLY. Install under device/asus/p00a/audio after parent review.
# This guard is intentional: the delivered routes.c is unqualified and cannot
# produce sound. Do not set the variable until a new reviewed route revision.
ifneq ($(P00A_AUDIO_ROUTE_QUALIFIED),true)
$(error P00A audio routes are unqualified; review the route ledger before integration)
endif
PRODUCT_PACKAGES += \
    audio.primary.mt8163 \
    libtinyalsav2 \
    android.hardware.audio.service \
    android.hardware.audio@7.1-impl \
    android.hardware.audio.effect@7.0-impl \
    p00a_audio_policy_configuration \
    p00a_audio_policy_volumes \
    p00a_audio_effects
DEVICE_MANIFEST_FILE += device/asus/p00a/audio/staging/vintf/audio.xml
# Include board-audio.mk from BoardConfig.mk before Soong config is frozen.
# Existing wrapper owns its init_rc. No second service or effects are added.
