# SPDX-License-Identifier: Apache-2.0
# Experimental SDK 37 / shipping API 23 product. The upstream service creates
# a real SOFTWARE Keymaster; keystore2 uses its existing legacy adapter.
# keystore2 and hwservicemanager are already inherited by this product.
PRODUCT_PACKAGES += android.hardware.keymaster@4.0-service

# This product has no persistent /metadata. Use the supported post-/data APEX
# activation path; do not pin updated APEX extents in nonexistent metadata.
# This does not bypass signature verification or the keystore module-hash wait.
PRODUCT_SYSTEM_PROPERTIES += apexd.config.use_fiemap=false
