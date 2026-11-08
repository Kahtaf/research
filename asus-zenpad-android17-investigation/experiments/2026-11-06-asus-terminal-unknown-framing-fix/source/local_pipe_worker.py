"""Fixed local source-only pipe boundary. No target, network or arbitrary path."""
import sys
from sources import LOCAL_PROFILES
from worker import serve

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in LOCAL_PROFILES:
        raise ValueError('fixed local profile required')
    serve(LOCAL_PROFILES[sys.argv[1]], sys.stdin.buffer, sys.stdout.buffer)
