package com.kahtaf.asuswifisetup;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.system.Os;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class MainActivity extends Activity {
    private static final String BINARY_SHA = "328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827";
    private static final String SCRIPT_SHA = "75bc4f393a44c8dfb4663b8da53e7986e1dca47ddf6b0c18472f39b2c523e05b";
    private static final String FINGERPRINT = "asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys";
    private static final AtomicBoolean BUSY = new AtomicBoolean();
    private static volatile String report = "Ready. Nothing runs until you tap the button.";
    private static final int LIMIT = 24576;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private TextView output;
    private Button enable;
    private String displayed;
    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            if (!report.equals(displayed)) { displayed = report; output.setText(displayed); }
            enable.setEnabled(!BUSY.get());
            ui.postDelayed(this, 400);
        }
    };

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (20 * getResources().getDisplayMetrics().density);
        layout.setPadding(pad, pad, pad, pad);
        TextView title = new TextView(this);
        title.setText("ASUS Wi-Fi debugging"); title.setTextSize(24);
        layout.addView(title);
        TextView explanation = new TextView(this);
        explanation.setText("For this owner's stock ASUS P00A_2 only.\n\n"
            + "One tap attempts temporary, on-demand root, saves authenticated ADB port 5555, "
            + "and restarts only adbd. The saved ADB setting persists; no root service is installed. "
            + "SELinux must start and finish Enforcing, and ADB authentication stays enabled.\n\n"
            + "App-context rooting has not been proved. Keep the tablet on your trusted Wi-Fi. "
            + "Accept the Mac's RSA debugging prompt only when you recognize it. "
            + "Do not run the Termux route at the same time.\n");
        layout.addView(explanation);
        enable = new Button(this); enable.setText("Enable Wi-Fi debugging");
        layout.addView(enable);
        output = new TextView(this); output.setTextSize(13); output.setTextIsSelectable(true);
        ScrollView scroll = new ScrollView(this); scroll.addView(output);
        layout.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(layout);
        enable.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                if (!BUSY.compareAndSet(false, true)) return;
                enable.setEnabled(false);
                report = "Checking this device…";
                final Context app = getApplicationContext();
                new Thread(new Runnable() {
                    @Override public void run() {
                        try { attempt(app); }
                        finally { BUSY.set(false); }
                    }
                }, "explicit-wifi-adb-attempt").start();
            }
        });
    }
    @Override public void onResume() { super.onResume(); ui.post(refresh); }
    @Override public void onPause() { ui.removeCallbacks(refresh); super.onPause(); }

    private static final class Snapshot {
        String serial, device, sdk, fingerprint, secure, enforcing, persist, service, ip;
        boolean exact() {
            return serial.equals("DEVICE_SERIAL_REDACTED") && device.equals("P00A_2")
                && sdk.equals("24") && fingerprint.equals(FINGERPRINT)
                && secure.equals("1") && enforcing.equals("Enforcing");
        }
        boolean configured() {
            return exact() && persist.equals("5555") && service.equals("5555");
        }
        String show() {
            return "serial=" + serial + "\ndevice=" + device + "\nSDK=" + sdk
                + "\nfingerprint=" + fingerprint + "\nro.adb.secure=" + secure
                + "\nSELinux=" + enforcing + "\npersist.adb.tcp.port=" + persist
                + "\nservice.adb.tcp.port=" + service + "\nwlan0 IPv4=" + ip + "\n";
        }
    }
    private static Snapshot inspect() throws Exception {
        Snapshot s = new Snapshot();
        s.serial = prop("ro.serialno"); s.device = prop("ro.product.device");
        s.sdk = prop("ro.build.version.sdk"); s.fingerprint = prop("ro.build.fingerprint");
        s.secure = prop("ro.adb.secure");
        s.enforcing = read("/system/bin/getenforce");
        s.persist = prop("persist.adb.tcp.port"); s.service = prop("service.adb.tcp.port");
        Result ip = command(new String[]{"/system/bin/ip", "-f", "inet", "addr", "show", "wlan0"}, null, 3000, true);
        Matcher m = Pattern.compile("\\binet\\s+(\\d+\\.\\d+\\.\\d+\\.\\d+)/").matcher(ip.output);
        s.ip = m.find() ? m.group(1) : "unavailable (check Wi-Fi connection)";
        return s;
    }
    private static String prop(String name) throws Exception { return read("/system/bin/getprop", name); }
    private static String read(String... argv) throws Exception {
        Result r = command(argv, null, 3000, true);
        if (r.exit == null || r.exit != 0 || r.truncated) throw new Exception("Cannot read " + argv[0]);
        return r.output.trim();
    }
    private static void attempt(Context app) {
        StringBuilder log = new StringBuilder();
        boolean attempted = false;
        Result root = null;
        try {
            Snapshot before = inspect();
            log.append("Before:\n").append(before.show()).append('\n');
            if (!before.exact()) { report = "REFUSED: device, authentication or SELinux check failed.\n\n" + log; return; }
            if (before.configured()) { report = ready("Already configured; no root attempt made.", before) + "\n" + log; return; }
            File sentinel = new File(app.getFilesDir(), "attempt-started");
            if (sentinel.exists()) {
                report = "REFUSED: an earlier attempt may have run. No automatic or repeated root attempt. "
                    + "Keep this app's data intact and ask the parent task to assess the result.\n\n" + log;
                return;
            }
            byte[] binary = asset(app, "mtk-su64", BINARY_SHA, 1024 * 1024);
            byte[] script = asset(app, "root-actions.sh", SCRIPT_SHA, 4096);
            File dir = new File(app.getFilesDir(), "native");
            if (!dir.isDirectory() && !dir.mkdir()) throw new Exception("Cannot create private native directory");
            Os.chmod(dir.getAbsolutePath(), 0700);
            File executable = new File(dir, "mtk-su64");
            try (FileOutputStream f = new FileOutputStream(executable)) {
                f.write(binary); f.getFD().sync();
            }
            Os.chmod(executable.getAbsolutePath(), 0700);
            try (InputStream f = new java.io.FileInputStream(executable)) {
                if (!sha(readBounded(f, 1024 * 1024)).equals(BINARY_SHA)) throw new Exception("Private binary hash mismatch");
            }
            Snapshot immediate = inspect();
            if (!immediate.exact()) throw new Exception("Device preflight changed; refusing execution");
            if (immediate.configured()) {
                report = ready("Already configured; no root attempt made.", immediate) + "\n" + log;
                return;
            }
            if (!sentinel.createNewFile()) throw new Exception("Attempt marker already exists; refusing execution");
            Os.chmod(sentinel.getAbsolutePath(), 0600);
            try (FileOutputStream f = new FileOutputStream(sentinel)) {
                f.write("One explicit attempt reserved; never retry automatically.\n".getBytes(StandardCharsets.UTF_8));
                f.getFD().sync();
            }
            attempted = true;
            report = "Attempt reserved. Running the pinned binary once; do not start the Termux route.\n\n" + log;
            root = command(new String[]{executable.getAbsolutePath(), "-c", "/system/bin/sh"}, script, 60000, false);
            log.append("Root process exit: ").append(root.exit == null ? "still running / unknown after 60 seconds" : root.exit)
                .append("\nCollected output (max 24 KiB):\n").append(root.output)
                .append(root.truncated ? "\n[output truncated]\n" : "\n");
        } catch (Exception e) {
            log.append("Error: ").append(e.getClass().getSimpleName()).append(": ").append(e.getMessage()).append('\n');
        }
        if (!attempted) { report = "No root process launched.\n\n" + log; return; }
        try {
            Snapshot after = inspect();
            log.append("\nIndependent after-check:\n").append(after.show());
            if (root != null && root.exit != null && root.exit == 0 && after.configured()) {
                report = ready("Settings applied and independently read back.", after) + "\n" + log;
            } else {
                report = "UNCERTAIN / NOT VERIFIED. No retry will be launched. "
                    + "A timed-out root process is not forcibly killed so its restoration trap can finish. "
                    + "Do not run the other route while this is unresolved.\n"
                    + (after.enforcing.equals("Enforcing") ? "SELinux reads Enforcing.\n" : "SELinux restoration is NOT confirmed; stop and report this result.\n")
                    + log;
            }
        } catch (Exception e) {
            report = "UNCERTAIN: independent after-check failed. No retry. SELinux/ADB state is unknown.\n"
                + log + "\n" + e.getClass().getSimpleName() + ": " + e.getMessage();
        }
    }
    private static String ready(String status, Snapshot s) {
        return status + "\nSELinux: Enforcing. ADB authentication: enabled.\n"
            + "wlan0 IPv4: " + s.ip + "\nPort: 5555\n"
            + "Ask the Mac owner to connect to this IP on port 5555, then accept the Mac's RSA debugging prompt. "
            + "Network reachability and RSA acceptance have not been verified by this app.\n";
    }
    private static byte[] asset(Context app, String name, String digest, int cap) throws Exception {
        try (InputStream in = app.getAssets().open(name)) {
            byte[] b = readBounded(in, cap);
            if (!sha(b).equals(digest)) throw new Exception("Embedded asset hash mismatch: " + name);
            return b;
        }
    }
    private static byte[] readBounded(InputStream in, int cap) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream(); byte[] b = new byte[4096]; int n;
        while ((n = in.read(b)) != -1) {
            if (out.size() + n > cap) throw new Exception("Asset exceeds size bound");
            out.write(b, 0, n);
        }
        return out.toByteArray();
    }
    private static String sha(byte[] b) throws Exception {
        StringBuilder s = new StringBuilder();
        for (byte v : MessageDigest.getInstance("SHA-256").digest(b)) s.append(String.format(java.util.Locale.US, "%02x", v & 255));
        return s.toString();
    }
    private static final class Capture implements Runnable {
        private final InputStream in;
        private final ByteArrayOutputStream out = new ByteArrayOutputStream();
        private boolean truncated;
        Capture(InputStream in) { this.in = in; }
        @Override public void run() {
            try {
                byte[] b = new byte[1024]; int n;
                while ((n = in.read(b)) != -1) {
                    synchronized (this) {
                        int keep = Math.min(n, LIMIT - out.size());
                        out.write(b, 0, keep);
                        if (keep < n) truncated = true;
                    }
                }
            } catch (Exception ignored) {
                synchronized (this) { truncated = true; }
            } finally { try { in.close(); } catch (Exception ignored) {} }
        }
        synchronized Result result(Integer exit) {
            return new Result(exit, new String(out.toByteArray(), StandardCharsets.UTF_8), truncated);
        }
    }
    private static final class Result {
        final Integer exit; final String output; final boolean truncated;
        Result(Integer exit, String output, boolean truncated) {
            this.exit = exit; this.output = output; this.truncated = truncated;
        }
    }
    private static Result command(String[] argv, byte[] stdin, long timeoutMs, boolean killOnTimeout) throws Exception {
        ProcessBuilder builder = new ProcessBuilder(argv).redirectErrorStream(true);
        builder.environment().remove("LD_PRELOAD"); builder.environment().remove("LD_LIBRARY_PATH");
        builder.environment().put("PATH", "/system/bin:/system/xbin");
        final Process p = builder.start();
        Capture capture = new Capture(p.getInputStream());
        Thread drain = new Thread(capture, "bounded-command-output"); drain.setDaemon(true); drain.start();
        try (OutputStream out = p.getOutputStream()) { if (stdin != null) out.write(stdin); }
        long deadline = android.os.SystemClock.elapsedRealtime() + timeoutMs;
        Integer exit = null;
        while (android.os.SystemClock.elapsedRealtime() < deadline) {
            try { exit = p.exitValue(); break; }
            catch (IllegalThreadStateException running) { Thread.sleep(50); }
        }
        if (exit == null && killOnTimeout) p.destroy();
        if (exit != null) drain.join(1000);
        return capture.result(exit);
    }
}
