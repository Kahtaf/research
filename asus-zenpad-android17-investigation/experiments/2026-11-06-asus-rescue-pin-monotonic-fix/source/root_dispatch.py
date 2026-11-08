"""Pinned helper loaded in an isolated module, every nested request authorized."""
import io
import subprocess
import types


def run(engine, commands, dispatch):
    source = engine.read_bounded(engine.HELPER)
    engine.require(engine.sha(source) == engine.HELPER_HASH, 'Root helper source drift')
    helper = types.ModuleType('exact_rescue_pinned_root_helper')
    helper.__file__ = str(engine.HELPER)
    exec(compile(source, helper.__file__, 'exec'), helper.__dict__)
    stdout, stderr = io.StringIO(), io.StringIO()
    helper.sys = types.SimpleNamespace(stdin=io.StringIO(commands), stdout=stdout, stderr=stderr)

    class CheckedADB:
        def request(self, args, **kwargs):
            engine.require(args[:len(helper.ADB)] == helper.ADB, 'Unexpected nested command')
            return dispatch(args, script=kwargs.get('input'), timeout=kwargs['timeout'])

        def check_output(self, args, *, text, timeout):
            engine.require(text is True, 'Unexpected helper encoding')
            result = self.request(args, timeout=timeout)
            stderr.write(result.stderr)
            if result.returncode:
                raise engine.UncertainTransport('Nested helper query failed')
            return result.stdout

        def run(self, args, *, timeout, check=False, stdout=None, input=None,
                text=False, capture_output=False):
            result = self.request(args, input=input, timeout=timeout)
            # Preserve aggregate stderr even when helper requests captured output.
            stderr.write(result.stderr)
            if not capture_output:
                (stdout if stdout is not None else helper.sys.stdout).write(result.stdout)
            if check and result.returncode:
                raise engine.UncertainTransport('Nested helper staging/precheck failed')
            # main() prints captured stderr itself. Avoid counting it twice.
            if capture_output:
                return subprocess.CompletedProcess(args, result.returncode, result.stdout, '')
            return result

    helper.subprocess = CheckedADB()
    try:
        code = helper.main()
        engine.require(type(code) is int and 0 <= code <= 255, 'Invalid helper completion')
        return subprocess.CompletedProcess(['pinned-helper'], code, stdout.getvalue(), stderr.getvalue())
    except (SystemExit, UnicodeError, OSError, ValueError, engine.Refused, engine.UncertainTransport) as exc:
        raise engine.UncertainTransport('Root helper completion uncertain: ' + str(exc) +
                                        '; aggregate stderr=' + stderr.getvalue()) from exc
