# Parent handoff

Actual signed APK: `artifacts/asus-wifi-adb-development.apk` (57,876 bytes).

APK SHA-256: `374ba0d1327572831c280da5d471d98e9bb48444943bb6e01768a75dd031235c`

Embedded unchanged mtk-su64 SHA-256: `328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827`

Embedded unchanged root-actions.sh SHA-256: `75bc4f393a44c8dfb4663b8da53e7986e1dca47ddf6b0c18472f39b2c523e05b`

SDK24 v2 signature verification, manifest/minSDK24/targetSDK24/no-permissions and packaged-asset hashes passed. Public evidence is in `evidence/`; source and build scripts are included. Signing key stays in the ignored private directory of this spike's isolated builder prefix, not in the deliverables.

Parent may serve this APK using its existing LAN_ADDRESS_REDACTED:8765 workflow. The owner must explicitly tap **Enable Wi-Fi debugging**; install/open has no root action. Do not operate this and the pending Termux route concurrently. A one-attempt marker prevents automatic/repeated execution; preserve app data after uncertainty. A native timeout is reported as uncertain and does not forcibly interrupt the restoration trap. Read the app result and accept only the recognized Mac RSA prompt.

App-context rooting remains unproved. No device/ADB/root/emulator/server operation was done here. No parent build/process/cache/log/lock or lifecycle/network/firewall changes were made; originals remain byte-identical.
