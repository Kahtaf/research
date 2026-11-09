# Experiment54: read-only dashboard power status

The existing local dashboard now displays the primary tablet battery percent, charging state and USB POWER status in a compact line above the original status table. /health returns the same original fields plus a power object. Responses use Cache-Control:no-store. Refresh remains manual; no extra polling or repeated SQLite writes were added.

Only three standard attributes are read: power_supply/battery/capacity, battery/status, usb/online. The separate absent pack_bat supply reports-1 and is not used. Missing/invalid values display unavailable/Unknown rather than interrupting the dashboard. No charger/ADC/calibration/property writes. The original kernel getter exposes stored battery status/capacity fields; no engineering calibration controls were queried.

Actual tablet validation:83%,Charging,USB power connected. Fresh /health values matched the actual sysfs values; rendered HTML contained the power line and no-store header. Existing saved requests increased across a controlled dashboard-only service restart (73 at verification). A consistent SQLite backup plus quick_check=ok and original application source were saved privately under SD private/before-dashboard-power before replacement. Owner Firefox shows the updated dashboard. SSH, desktop and audio services were not restarted for this change.

USB power status does NOT establish USB DATA continuity or repair the physically loose port. Keep the tablet stationary and use Wi-Fi SSH. Raw inventory and install/result logs remain ignored under private/live. No packages, internal partitions, SD layout, credentials, profile preferences or factory calibration changed.
