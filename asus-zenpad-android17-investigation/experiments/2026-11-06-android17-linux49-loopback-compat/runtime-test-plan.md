# Real socket qualification plan — NOT RUN

Run only after reviewed implementation, isolated changed-object compilation and a separately authorized kernel runtime step. This document does not authorize device, full-kernel, active AOSP or cloud actions. All new remote files must live below `/srv/android/asus-loopback-compat-20261106`; never invoke old scripts over the old prefix. Budget the entire new fixture to512MiB. Each action: one CPU,1GiB maximum guest/process memory, finite CPU and wall deadlines no greater than15min, `-nic none`, no external guest networking. Use a new run label each time. Record timeout/incomplete/missing setup as failure, not a skip or success. Keep old failure evidence.

## Inputs and mandatory setup

Record exact Image/config/source/patch, loader, BPF ELF, map ABI, guest compiler/probe and QEMU pins for each run. Hash only new/selected inputs. Use actual SDK3701 property storage; retain truthful kernel4.9 identity. Do not supply a readiness property, suppress a mandatory load failure, downgrade the policy API selection, disable flags or substitute HASH for active LRU storage. Ensure actual egress and creator programs are loaded, their real IDs/tags/pins and cgroup attachments are queried, and storage/BTF map metadata matches the128-byte value ABI. Fail setup if a required pin, attachment or value is absent.

Read back checks=true and actual permission migration state. Populate documented full-UID permission chunks using production packing, independent readback and a saved original map value; cleanup belongs only to the newly owned fixture. Metrics on/off are additional controlled tests; no disabling an enabled production flag to obtain the main passing result. Same-profile and checks-disabled are explicitly labeled **controls** and do not count as cross-profile enforcement. Restore prior state after each control. Retain physical FILE_LOCKING=y and the separately owned BLK_CGROUP decision; do not copy the virtual config to hardware.

## Identity and observation protocol

For each case, create receiver sockets in a child after setting real UID/GID and necessary INTERNET group. Record credentials, cgroup and netns inode. Send the FD over SCM_RIGHTS to the controller, validate ancillary length/type/truncation, fstat inode UID, source-child exit status and getsockname family/address/port. Close the creator's copy and exit; controller retains the sole intended FD. Create sender under the stated UID separately. Every payload carries a fresh unpredictable nonce; verify exact payload and no stale receive. Record syscall return and errno only when it failed, poll/receive result and time bounds. Do not accept a send error alone without confirming the receiver did not get the packet. Egress UDP policy denial must be `sendto=-1,errno=EPERM`; controls must deliver the nonce. TCP denial checks use nonblocking connect/SO_ERROR and a bounded accept window, preserving actual cgroup SYN-drop behavior without assuming UDP-style synchronous EPERM.

Query actual storage through socket FD where the API permits: creator UID/GID/cookie and existence. This is an independent identity check, not an excuse to insert missing storage from the test. Null storage and allocation failure are separate source-defined fail-open behavior tests; they cannot satisfy the main gate. Capture all children through waitpid with finite timeouts; no process polling or external signals to active owned builds.

## Main IPv4/IPv6 packet matrix

Run every row for AF_INET127.0.0.1 and AF_INET6::1, UDP connected/unconnected sender and TCP listener/SYN. Use loopback ifindex1 as the original source requires and record it. Repeat UID directions to expose asymmetric permission handling.

| Sender → creator receiver | Permissions | Required outcome with checks=true |
|---|---|---|
|10001 →110002|none|deny; baseline run-r18 reproduced first, then fixed with same identities/setup|
|10001 →10002|none|allow, same profile|
|10001 →10001|none|allow, same UID|
|10001 →110001|none|deny, same appId across profiles|
|10001 →110001|sender OR_PROFILES|allow|
|10001 →110002|sender OR_PROFILES|deny|
|10001 →110002|sender FULL|allow|
|10001 →110002|receiver FULL only|deny|
|10001 →110002|sender FORCE only / receiver FORCE only|deny|
|10001 →110002|FORCE+FULL together on either endpoint|allow|
|10001 →110002|USE_LOOPBACK only on either/both|deny under this pinned TODO-containing policy|
|system appId at either endpoint, including another profile|none|allow per is_system_uid|
|10001 →110002|none, checks=false CONTROL|allow; restore checks=true and read back before main case|

Also run no-INTERNET-group creation negative controls without replacing the normal UID/group setup, migration NO_INTERNET creation rejection for full UID, same-appId different-profile permission differences, and creation under both migration branches as controlled source-compatibility tests. Do not change the main run's migration flag to evade a failure.

Address/parser cases: IPv4-mapped IPv6/dual-stack listener, wildcard versus specific bind, connected versus unconnected UDP receiver, TCP SYN/SYN-ACK and established non-SYN bypass, TCP TIME_WAIT/request sockets, no listener, unsupported IP protocols, IPv4 options, IPv6 extension headers and parse failure. Use original behavior as oracle, including deliberate allow paths. Do not invent universal ICMP or established-TCP isolation the production source does not implement.

## FD and credential lifecycle

* Create UID110002 receiver; SCM_RIGHTS to UID10001 or root; creator exits. Stored receiver UID remains110002. Sender10001 must still be denied after cache expiry.
* Duplicate/fork/exec and transfer the FD twice, closing intermediate owners. No reference leak, reset or re-attribution. Close one duplicate while another receives; final close destroys storage exactly once.
* Privileged fchown of receiver FD changes inode/sk_uid; creator-storage UID remains110002 and receiver classification stays110002. For sender FD fchown, honor the actual `bpf_get_socket_uid` sender identity used by the production body; do not incorrectly require immutable sender creator identity.
* Change process credentials after socket creation; test sender and receiver independently. Current task credentials must not overwrite existing socket storage. Test privileged fsuid variation separately; compare current_uid helper and sock inode identity rather than assuming they are equal.
* Accepted TCP sockets/clone paths: verify map clone flags, NULL initialization before failure branches, absence of unintended parent-storage aliasing and original SYN-only receiver policy. Inject allocation/filter-charge failure at each early clone bailout; parent storage must remain intact, partial new storage must be freed.
* Close/rebind same address/port under another UID, including rapid FD-number/pointer recycling. After the source-defined UDP cache window, classification must use the new receiver. Within the window, compare to original cached semantics, not an invented instantaneous guarantee.
* Remove/reinstall numeric UID permission entries while sockets survive; storage retains creator numeric UID, while permission decisions after expiry follow current full-UID chunks. Explicitly cover chunk boundaries UID1151/1152, u64 edges8/9 and last representable UID1036799.

## Cache, metrics and concurrency

Prime allow and deny UDP entries. Change permissions/receiver identity and sample before10ms, at/after10ms, and after destination address/port changes. Test sender with/without storage, TCP non-SYN bypass and flags readback. Compare the unchanged original cache behavior. BOOTTIME expiry across suspend requires a separately authorized environment; host fake-clock tests do not prove it.

Run concurrent senders on a shared socket, create/close/rebind, map updates/deletes, FD lookup/replacement and map unpin/final close. Preserve lockless source cache behavior without asserting stronger linearizability. Under RCU/map-free stress, require no UAF, double-free, dangling map/storage member, refcount underflow or leaked socket/map memory after bounded drain. Exercise allocation failure and charge rollback. Metrics enabled must preserve reserve/submit/discard balance, throttling by full event key, LRU eviction/capacity and actual allow/deny event values. Ringbuf mmap/poll/consumer teardown needs actual syscalls, not host doubles.

One-CPU runs cover scheduling interleavings, **not SMP memory-order races**. Full concurrency qualification remains blocked until an explicitly authorized later SMP test; do not exceed this task's oneCPU bound. KASAN/lockdep/RCU diagnostics likewise need an appropriate separately built runtime, not claims from the Darwin sanitizer test.

## Network namespaces and selection

Create two isolated netns with identical127.0.0.1/::1 tuples and different receiver creator UIDs. CURRENT_NETNS must select the context namespace, never a same-tuple socket in the other namespace. Test teardown while references and maps remain, relative namespace IDs, negative CURRENT_NETNS and other signed-negative contract values, unavailable IDs, reserved high bits, flags and tuple lengths. Namespace failure must return the real helper result without consulting init_net. User namespace UID conversion requires explicit oracle checks as creator helper and sender UID helper use their documented namespace conversions.

Exercise SO_REUSEADDR/SO_REUSEPORT groups containing different creator UIDs, wildcard/specific listeners, bound-device sockets, v4/v6 selection and lookup racing removal. Compare selected socket/cookie with the unmodified upstream helper contract and eventual delivery; an egress lookup cannot be assumed identical to future receive selection during membership changes. Preserve original per-lookup selection rather than replacing it with deny-if-any/allow-if-any. All traffic stays inside the guest; any veth interface testing needs a revised bounded fixture and retains `-nic none`.

## Exit gates

1. Preserve and classify the old run-r18 two failures; new main cross-profile cases pass for both families without changed identities, permissions, flags or readiness.
2. Original positive and negative controls pass; setup or helper failure is not a pass. Verifier malicious programs reject for the expected safety reason while valid production programs load unchanged in policy behavior.
3. Actual source/config/tool/ELF pins, map metadata, real attachments, payload/syscall results and all failed attempts are retained. No whole-image/source copy or rehash is needed.
4. Core policy/API tests from the old qualified handoff are rerun only by their owner against a reviewed integrated kernel. New loopback qualification does not rewrite old evidence or assume separately owned three-BPF outputs qualified.
5. Android init/property service, BpfNetMaps real permission/UID lifecycle and service integration remain separate gates. No physical, flash, WiFi or Google GO follows from these socket tests.
