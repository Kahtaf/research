#!/usr/bin/env python3
"""Run a graphics builder command using the existing, host-verified SSH identity."""
import subprocess
import sys

SSH = ['ssh', '-i', '~/.ssh/asus_p00a_android17', '-o', 'IdentitiesOnly=yes',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'HostKeyAlias=compute.8549823276971553556',
       '-o', 'UserKnownHostsFile=~/.ssh/google_compute_known_hosts', 'android@IP_REDACTED']

if __name__ == '__main__':
    sys.exit(subprocess.run(SSH + [sys.argv[1]]).returncode)
