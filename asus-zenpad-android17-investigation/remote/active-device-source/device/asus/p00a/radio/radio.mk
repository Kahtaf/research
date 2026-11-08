# Also inherit connectivity-base.mk and wifi-sta-trial.mk from connectivity spike.
PRODUCT_PACKAGES += p00a-wmt
# Deliberately no enable property: source staging does not authorize activation.
# Set persist.vendor.p00a.radio.enable=1 only for the reviewed persistent profile.
