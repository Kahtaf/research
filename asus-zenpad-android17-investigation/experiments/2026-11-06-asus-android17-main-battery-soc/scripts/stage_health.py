#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def change(p,fn):
 src=R/'source/platform'/p; out=R/'integration/platform'/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(fn(src.read_text()))
change('hardware/interfaces/health/aidl/default/include/health-impl/Health.h',lambda s:s.replace('    virtual void UpdateHealthInfo(HealthInfo* health_info);','''    virtual void UpdateHealthInfo(HealthInfo* health_info);

    // Optional checked platform snapshot. Called by final getHealthInfo before
    // returning success. Errors propagate through update and callback delivery.
    // The default preserves existing products; a board can reject unavailable
    // mandatory measurements without overriding the final aggregate method.
    virtual ndk::ScopedAStatus ReadBatterySnapshot(HealthInfo* health_info);'''))
change('hardware/interfaces/health/aidl/default/Health.cpp',lambda s:s.replace('''    UpdateHealthInfo(out);

    return ndk::ScopedAStatus::ok();''','''    UpdateHealthInfo(out);

    auto status = ReadBatterySnapshot(out);
    if (!status.isOk()) {
        // A failed binder method has no valid aggregate output. Callers must
        // inspect status; update/registerCallback already do so.
        *out = HealthInfo{};
    }
    return status;''',1).replace('''int32_t Health::getFullChargeUah() const {''','''ndk::ScopedAStatus Health::ReadBatterySnapshot(HealthInfo*) {
    return ndk::ScopedAStatus::ok();
}

int32_t Health::getFullChargeUah() const {''',1))
change('hardware/interfaces/health/aidl/default/HalHealthLoop.cpp',lambda s:s.replace('''    CHECK(res.isOk()) << "getHealthInfo() on the health HAL implementation failed with "
                      << res.getDescription();''','''    if (!res.isOk()) {
        LOG(WARNING) << "getHealthInfo() unavailable; retaining callbacks and retrying: "
                     << res.getDescription();
        // Do not deliver an invalid aggregate or terminate the service. Keep
        // periodic updates running, using the last observed charger state.
        AdjustWakealarmPeriods(charger_online());
        return;
    }''',1))
# Even with the service's pre-registration sample gate, hardware may fail
# between registration and the first callback. Avoid continuing boot with null
# mHealthInfo after the existing single timeout; do not invent initial data.
def framework(s):
 old='''        if (mHealthInfo == null) {
            Slog.i(TAG, "health: Waited " + (SystemClock.uptimeMillis() - beforeWait)
                    + "ms for callbacks. Waiting another " + HEALTH_HAL_WAIT_MS + " ms...");
            mConditionVariable.block(HEALTH_HAL_WAIT_MS);
        }'''
 new='''        while (true) {
            synchronized (mLock) {
                if (mHealthInfo != null) {
                    break;
                }
            }
            Slog.w(TAG, "health: No valid initial battery sample after "
                    + (SystemClock.uptimeMillis() - beforeWait)
                    + "ms; waiting another " + HEALTH_HAL_WAIT_MS + " ms");
            mConditionVariable.block(HEALTH_HAL_WAIT_MS);
        }'''
 assert old in s
 return s.replace(old,new,1)
change('frameworks/base/services/core/java/com/android/server/BatteryService.java',framework)
print('Staged checked Health hook, retrying loop and initial-framework-data gate.')
# The initial manual update can race a sensor failure after registration.
# Unlike scheduleUpdate, this caller originally caught only RemoteException.
change('frameworks/base/services/core/java/com/android/server/health/HealthRegCallbackAidl.java',
       lambda s:s.replace('import android.os.RemoteException;',
                          'import android.os.RemoteException;\nimport android.os.ServiceSpecificException;').replace(
'''        } catch (RemoteException e) {
            Slog.e(TAG, "health: cannot update after registering health info callback", e);''',
'''        } catch (RemoteException | ServiceSpecificException e) {
            // Registration remains active. The HAL loop retries and sends the
            // first valid sample when the measurement/model recovers.
            Slog.e(TAG, "health: cannot update after registering health info callback", e);''',1))
