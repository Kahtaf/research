"""Owned host pipes only. Deadlines are parent policy, never hardware defaults."""
from dataclasses import dataclass
import math
import os
import selectors
import stat
import time


class DeadlineExpired(TimeoutError):
    pass


class PoisonedSession(RuntimeError):
    pass


def positive(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError('explicit positive finite budget required')
    return float(value)


@dataclass(frozen=True)
class Phase:
    name: str
    deadline: float
    message_seconds: float

    def __post_init__(self):
        positive(self.deadline)
        positive(self.message_seconds)

    def check(self):
        if time.monotonic() >= self.deadline:
            raise DeadlineExpired(self.name + ': absolute phase budget expired')

    def message_deadline(self):
        self.check()
        return min(self.deadline, time.monotonic() + self.message_seconds)


class Budgets:
    """Parent constructs once; phases cannot be restarted to extend a deadline."""
    NAMES = frozenset({'control', 'source_preflight', 'reconciliation',
                       'transfer', 'whole_image_hash'})

    def __init__(self, limits):
        if type(limits) is not dict or set(limits) != self.NAMES:
            raise ValueError('all distinct parent phase budgets required')
        self.limits = {}
        for name, pair in limits.items():
            if type(pair) not in (list, tuple) or len(pair) != 2:
                raise ValueError('phase seconds and message seconds required')
            self.limits[name] = (positive(pair[0]), positive(pair[1]))
        self.started = set()

    def start(self, name):
        if name in self.started:
            raise ValueError('phase already consumed')
        self.started.add(name)
        seconds, message = self.limits[name]
        return Phase(name, time.monotonic() + seconds, message)


class PipeSession:
    """One consumed transport; a timeout/EOF/unknown result is terminal.

    Descriptors must be owned unbuffered pipes/socketpairs. No reconnect or
    protocol cleanup. Closing a host pipe says nothing about accepted target work.
    """
    def __init__(self, reader, writer, phase, *, stderr=None, process=None):
        self.reader, self.writer = reader, writer
        self.stderr, self.process = stderr, process
        self.dead = False
        self.outcome = 'UNOBSERVED'
        self.commit_receipt = None
        self.phase_completed = False
        self.possible_partition_modification = False
        self.stderr_tail = bytearray()
        self.pending = None
        self.phase = phase
        self.closed = False
        try:
            self.check()
            for fd in {reader, writer, stderr} - {None}:
                mode = os.fstat(fd).st_mode
                if not (stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)):
                    raise ValueError('owned unbuffered pipe/socket required')
                os.set_blocking(fd, False)
                self.check()  # Guard work cannot hide phase expiry.
        except BaseException:
            self.poison()
            raise

    def poison(self):
        self.dead = True
        self.outcome = 'UNKNOWN'

    def check(self, deadline=None):
        if self.dead or self.closed:
            raise PoisonedSession('terminal session; no further requests')
        try:
            self.phase.check()
            if deadline is not None and time.monotonic() >= deadline:
                raise DeadlineExpired(self.phase.name + ': absolute message budget expired')
        except DeadlineExpired:
            self.poison()
            raise

    def complete_phase(self):
        """Check after the last guard/publication; completion permits later idle."""
        try:
            self.check()
            if self.pending is not None:
                raise PoisonedSession('cannot complete a pending request')
            self.phase_completed = True
        except BaseException:
            self.poison()
            raise

    def set_phase(self, phase):
        if self.dead or self.closed:
            raise PoisonedSession('terminal session; no phase restart')
        if not self.phase_completed:
            self.complete_phase()  # Validate outgoing phase before replacing it.
        self.phase = phase
        self.phase_completed = False
        try:self.check()
        except BaseException:self.poison();raise

    def _drain_stderr(self):
        if self.stderr is None:
            return
        try:
            data = os.read(self.stderr, 16384)
        except (BlockingIOError, InterruptedError):
            return
        if not data:
            self.stderr = None
        elif len(self.stderr_tail) < 65536:
            self.stderr_tail.extend(data[:65536 - len(self.stderr_tail)])

    def _wait(self, fd, event, deadline):
        self.check(deadline)
        with selectors.DefaultSelector() as selector:
            selector.register(fd, event)
            if self.stderr is not None and self.stderr != fd:
                selector.register(self.stderr, selectors.EVENT_READ)
            while True:
                self.check(deadline)
                try:
                    ready = selector.select(max(0, deadline - time.monotonic()))
                except InterruptedError:
                    continue
                self.check(deadline)
                usable = False
                for key, _ in ready:
                    if key.fd == fd:
                        usable = True
                    else:
                        self._drain_stderr()
                        if self.stderr is None:
                            selector.unregister(key.fd)
                self.check(deadline)
                if usable:
                    return
                # Only inspect the explicitly owned child, never system processes.
                if self.process is not None and self.process.poll() is not None:
                    raise EOFError('owned child exited; completion UNKNOWN')

    def read_exact(self, length, deadline):
        self.phase_completed = False
        result = bytearray()
        try:
            self.check(deadline)
            while len(result) < length:
                self._wait(self.reader, selectors.EVENT_READ, deadline)
                self.check(deadline)
                try:
                    data = os.read(self.reader, length - len(result))
                except (BlockingIOError, InterruptedError):
                    continue
                self.check(deadline)
                if not data:
                    raise EOFError('host pipe EOF; completion UNKNOWN')
                result.extend(data)
            self.check(deadline)
            return bytes(result)
        except BaseException:
            self.poison()
            raise

    def write_exact(self, data, deadline):
        self.phase_completed = False
        view = memoryview(data)
        try:
            self.check(deadline)
            while view:
                self._wait(self.writer, selectors.EVENT_WRITE, deadline)
                self.check(deadline)
                try:
                    n = os.write(self.writer, view)
                except (BlockingIOError, InterruptedError):
                    continue
                self.check(deadline)
                if n <= 0:
                    raise OSError('short host pipe write')
                view = view[n:]
            self.check(deadline)
        except BaseException:
            self.poison()
            raise

    def send(self, header, payload=b'', *, mutation=False):
        try:
            self.check()
            if self.pending is not None:
                raise PoisonedSession('previous request completion unknown')
            self.phase_completed = False
            self.pending = self.phase.message_deadline()
            if mutation:
                self.possible_partition_modification = True
            # One absolute deadline for header + payload + corresponding reply.
            self.write_exact(header, self.pending)
            self.write_exact(payload, self.pending)
        except BaseException:
            self.poison()
            raise

    def receive(self, header_size, decode, *, final=True):
        try:
            self.check()
            self.phase_completed = False
            deadline = self.pending if self.pending is not None else self.phase.message_deadline()
            header = self.read_exact(header_size, deadline)
            op, length = decode(header)
            data = self.read_exact(length, deadline)
            self.check(deadline)
            self.pending = None if final else deadline
            return op, data
        except BaseException:
            self.poison()
            raise

    def read_stream_end(self, limit):
        """Bounded plain features output or post-protocol child/stderr drain."""
        self.phase_completed = False
        try:
            self.check()
            if self.pending is not None:
                raise PoisonedSession('pending request; cannot finish stream')
            deadline = self.phase.message_deadline()
            data = bytearray()
            with selectors.DefaultSelector() as selector:
                selector.register(self.reader, selectors.EVENT_READ)
                if self.stderr is not None:
                    selector.register(self.stderr, selectors.EVENT_READ)
                while selector.get_map():
                    self.check(deadline)
                    try:
                        ready = selector.select(max(0, deadline - time.monotonic()))
                    except InterruptedError:
                        continue
                    self.check(deadline)
                    for key, _ in ready:
                        if key.fd == self.reader:
                            try:
                                block = os.read(self.reader, 4096)
                            except (BlockingIOError, InterruptedError):
                                continue
                            self.check(deadline)
                            if not block:
                                selector.unregister(key.fd)
                            elif len(data) + len(block) > limit:
                                raise ValueError('unexpected/excess host stream output')
                            else:
                                data.extend(block)
                        else:
                            self._drain_stderr()
                            if self.stderr is None:
                                selector.unregister(key.fd)
                        self.check(deadline)
            return bytes(data)
        except BaseException:
            self.poison()
            raise

    def close(self):
        """Seal the session; creating parent owns descriptor closure and child reap."""
        if not self.closed:
            self.closed = True
            self.dead = True
            # File objects/process ownership stays with the creating parent.


# Failed finite host cleanup keeps ownership reachable for explicit host cleanup.
# This is never a transport reconnect/retry queue.
UNREAPED_CHILDREN = {}


def reap_owned(process, grace):
    """Finite host-child cleanup. Termination never implies target cancellation."""
    import subprocess
    grace = positive(grace)
    UNREAPED_CHILDREN[process.pid] = process
    close_error = None
    for stream in (process.stdin, process.stdout, process.stderr):
        try:
            if stream is not None and not stream.closed:
                stream.close()
        except BaseException as error:
            if close_error is None:close_error = error
    try:
        try:
            result = process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                result = process.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                process.kill()
                result = process.wait(timeout=grace)
        if process.returncode is None:
            raise RuntimeError('owned child reaping not confirmed')
        if close_error is not None:raise close_error
        return result
    finally:
        if process.returncode is not None:
            UNREAPED_CHILDREN.pop(process.pid, None)
