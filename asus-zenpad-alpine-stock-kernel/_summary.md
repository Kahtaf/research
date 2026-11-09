Attempting to revitalize the ASUS ZenPad Z380M, this project successfully deploys [Alpine Linux](https://alpinelinux.org/) aarch64 on the device's original 3.18.35 kernel. By building upon the [kaantcp/z380m-alpine](https://github.com/kaantcp/z380m-alpine) foundation, the implementation achieves a functional microSD-based boot environment that preserves the stock Android partition structure for easy rollback. The current state supports persistent SSH access, stable Wi-Fi connectivity, and an Xorg-based desktop featuring Firefox with working multi-touch gestures. While core hardware interactions are established, development is currently paused with audio, Bluetooth, and sensor rotation remaining in a prototype stage.

*   Persistent microSD boot with stable SSH identity and Python/SQLite support.
*   Native Wi-Fi initialization and DHCP renewal using stock Android dependencies.
*   Functional Firefox ESR browser with multi-finger scrolling and automatic on-screen keyboard.
*   Safe PulseAudio path implementation to circumvent ALSA mmap kernel instability.
