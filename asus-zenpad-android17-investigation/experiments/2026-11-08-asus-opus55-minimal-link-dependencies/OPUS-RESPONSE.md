**Verdict: proceed with one olddefconfig gate and one incremental continuation.** All three fixes finish the same reduction you already approved. Each one either restores an ancestor setting or completes a removal you already reviewed. None of them changes the protection closure. One premise needs correcting first: "just set NET=y" is not a single bit.

**1. Tracing core (FTRACE=y, ENABLE_DEFAULT_TRACERS=y): justified.**
- `tracing_record_cmdline` comes from TRACING, and ENABLE_DEFAULT_TRACERS selects TRACING only while GENERIC_TRACER is off. So FUNCTION_TRACER and SCHED_TRACER must stay off.
- **Source fact to check before building:** whether the vendor `kernel/trace/` patches, or MET Kconfig, turn tracing or events on at boot. Look for anything like `MTK_FTRACE_DEFAULT_ENABLE`, an MTK sched-tracer option, or a forced trace buffer size.
- With those off, the ring buffer stays minimal and static tracepoints stay dormant. If any of them is on, pin it off. If it can't be pinned off, stop.

**2. VS_BACKLIGHT_COOLER=n: justified.** It finishes the backlight removal you already reviewed. At the gate, confirm that `virtual_sensor_cooler_backlight.o` is no longer built. Also confirm that nothing outside that file references its symbols, apart from bind-by-name cooler tables. An unbound cooler name is harmless. CPU and PMIC critical shutdown don't depend on it.

**3. NET=y: justified, but this is where the bad premise is.** NET=y makes many symbols visible, and some of them default to y. Examples are WIRELESS, NETDEVICES/ETHERNET, NETLINK-based uevent, and probably MTK connectivity or CCCI modem options gated on NET. olddefconfig will quietly accept those defaults. Any network symbol that turns on has to be pinned off explicitly. The one runtime difference you're accepting is that uevents also go out over netlink. Confirm that UEVENT_HELPER behaviour stays the same.

**Accept the gate only if:**
- The resolved-config diff contains only the intended symbols plus their mechanical closure (TRACING, NOP_TRACER, EVENT_TRACING, RING_BUFFER, TRACEPOINTS, and the NET core with UNIX, INET and PACKET still off). Every other new symbol is listed and either pinned off or shown to be core-only.
- No new driver binds a DT compatible, and none of the 99 disabled paths change.
- DT, cmdline, initramfs and helper hashes are identical.

**Accept the continuation only if:**
- The link finishes with zero undefined symbols and no new warnings.
- `nm` shows `tracing_record_cmdline` and `register_netdevice_notifier` defined, and `setMaxbrightness` and the cooler object absent.

**Stop if:**
- Any vendor tracing default-enable option turns on.
- Any WLAN, BT, wireless, CCCI, connectivity or netdevice driver turns on.
- Any new undefined symbol or new substantive error appears.
- Any source edit is needed.
- Anything in the protection closure, or the battery, PMIC, thermal or CPU settings, changes.

A clean link proves only that the build is consistent. It says nothing about how the device will behave.