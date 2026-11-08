"""Run the pinned helper with each real ADB request behind HostIO authorization."""
import io
import subprocess
import types
import fixed as F
import observer as O


def run(argv, commands, host, authorize):
    F.require(callable(authorize), 'Nested helper authorization callback required')
    F.require(argv == [__import__('sys').executable, str(F.E.HELPER)], 'Only the pinned root helper is accepted')
    source = F.read(F.E.HELPER)
    F.require(F.sha(source) == F.E.HELPER_HASH, 'Pinned root helper changed')
    helper = types.ModuleType('asus_exact_root_helper_checked_dispatch')
    helper.__file__ = str(F.E.HELPER)
    exec(compile(source, str(F.E.HELPER), 'exec'), helper.__dict__)
    stdout, stderr = io.StringIO(), io.StringIO()
    # Replace only this fresh module's references. No process-global monkeypatch
    # or sys.argv mutation can race the read-only observer thread.
    helper.sys = types.SimpleNamespace(stdin=io.StringIO(commands), stdout=stdout, stderr=stderr)

    class CheckedADB:
        def dispatch(self, args, **kwargs):
            F.require(args[:len(helper.ADB)] == helper.ADB, 'Unexpected nested helper command')
            result = host.command(args, script=kwargs.get('input'), timeout=kwargs['timeout'],
                                  text=True, authorize=authorize)
            return result

        def check_output(self, args, *, text, timeout):
            F.require(text is True, 'Unexpected helper query encoding')
            result = self.dispatch(args, timeout=timeout)
            helper.sys.stderr.write(result.stderr)
            if result.returncode:
                raise O.Unavailable('Nested helper query failed; no retry')
            return result.stdout

        def run(self, args, *, timeout, check=False, stdout=None, input=None,
                text=False, capture_output=False):
            result = self.dispatch(args, input=input, timeout=timeout)
            if not capture_output:
                (stdout if stdout is not None else helper.sys.stdout).write(result.stdout)
                helper.sys.stderr.write(result.stderr)
            if check and result.returncode:
                raise O.Unavailable('Nested helper precheck/staging request failed; no retry')
            return result

    helper.subprocess = CheckedADB()
    try:
        code = helper.main()
    except SystemExit as exc:
        # Original CLI guard failures/ambiguous completion are terminal, as the
        # outer frozen engine's missing/disagreeing status previously required.
        raise O.Unavailable('Pinned root helper refused or completion unverified: ' + str(exc)) from exc
    F.require(type(code) is int and 0 <= code <= 255, 'Unexpected helper exit status')
    return subprocess.CompletedProcess(argv, code, stdout.getvalue(), stderr.getvalue())
