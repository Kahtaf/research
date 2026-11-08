"""Actual unchanged helper execution, mock OS effects, real HostIO dispatch gate."""
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('nested_dispatch_fixtures', HERE / 'test_faults.py')
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)
import root_dispatch as R
F, T = M.F, M.T


def response(argv, script):
    args = argv[3:]
    out = ''
    if args == ['get-serialno']:
        out = F.ENDPOINT + '\n'
    elif args[:2] == ['shell', 'getprop']:
        out = F.STOCK_PROPS[args[2]] + '\n'
    elif args == ['shell', 'getenforce']:
        out = 'Enforcing\n'
    elif script:
        root = re.search(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=', script).group(1)
        helper = re.search(r'ASUS_WIFI_ROOT_([0-9a-f]{32})=', script).group(1)
        out = 'ASUS_RECOVERY_RC_' + root + '=0\nASUS_WIFI_ROOT_' + helper + '=0\n'
    return subprocess.CompletedProcess(argv, 0, out, '')


class NestedDispatch(M.Base):
    def run_helper(self, host, check):
        return R.run([sys.executable, str(F.E.HELPER)],
                     F.E.root_envelope('FIXTURE_ONLY_NO_DEVICE_EFFECTS', 'a' * 32), host, check)

    def test_each_nested_dispatch_rechecks_after_prior_request_returns(self):
        for boundary in range(13):
            host = T.HostIO(self.root / str(boundary))
            calls = []
            expired = [False]

            def check():
                if expired[0]: raise F.AuthorizationExpired('fixture review expired')

            def process(argv, **kwargs):
                calls.append((argv, kwargs.get('input')))
                result = response(argv, kwargs.get('input'))
                if len(calls) - 1 == boundary: expired[0] = True
                return result

            with patch.object(T.subprocess, 'run', side_effect=process):
                if boundary < 12:
                    with self.assertRaises(F.AuthorizationExpired): self.run_helper(host, check)
                else:
                    result = self.run_helper(host, check)
                    self.assertEqual(F.E.root_status(result, 'a' * 32), 0)
            self.assertEqual(len(calls), boundary + 1)
            if boundary <= 8:
                self.assertFalse(any(a[3:4] == ['push'] for a, _ in calls))
            if boundary <= 10:
                self.assertFalse(any(s is not None for _, s in calls))

    def test_actual_transport_uses_checked_helper_without_global_monkeypatch(self):
        host = T.HostIO(self.root / 'commands')
        journal = M.C.Journal(self.root, 'restore', 'OFFLINE')
        transport = T.Transport(self.root, journal, 'restore', M.RUN, 'restore', M.NEW, host)
        transport.authorization_check = lambda: None
        original_run = subprocess.run
        captured = []

        def process(argv, **kwargs):
            captured.append((argv, kwargs.get('input')))
            return response(argv, kwargs.get('input'))

        with patch.object(T.subprocess, 'run', side_effect=process):
            transport.write('stock')
        self.assertIs(subprocess.run, original_run)
        self.assertEqual(len(captured), 13)
        self.assertTrue(all(argv[:3] == ['adb', '-s', F.ENDPOINT] for argv, _ in captured))
        scripts = [script for _, script in captured if script is not None]
        self.assertEqual(len(scripts), 1)
        self.assertIn("trap 'setenforce 1' EXIT", scripts[0])
        self.assertIn(F.E.DEVICE_GUARD, scripts[0])
        self.assertEqual(re.findall(r'dd if=\S+ of=(\S+)', scripts[0]), [F.E.BLOCK])

    def test_nested_failure_is_uncertainty_not_inverse_trigger(self):
        host = T.HostIO(self.root / 'commands')
        with patch.object(T.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'fixture failed')):
            with self.assertRaises(M.O.Unavailable): self.run_helper(host, lambda: None)


if __name__ == '__main__': unittest.main()
