cat /run/asus-goodix/browser-proof.json 2>/dev/null || true
cat /run/asus-goodix/browser-workload.log 2>/dev/null || true
ps | grep -E 'browser-workload|firefox' | head -14
cat /run/asus-goodix/bridge.log
