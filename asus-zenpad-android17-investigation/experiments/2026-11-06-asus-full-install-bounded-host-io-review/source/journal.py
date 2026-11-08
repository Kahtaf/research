"""Bound evidence retained on the Mac, independent of image length or stderr noise."""
import threading


class BoundedJournal:
    def __init__(self, stream, limit=2 * 1048576):
        self.stream = stream
        self.limit = limit
        self.written = 0

    def write(self, text):
        size = len(text.encode('utf-8'))
        if self.written + size > self.limit:
            raise ValueError('journal capacity exceeded; stop and reconcile explicitly')
        self.written += size
        return self.stream.write(text)

    def flush(self):
        return self.stream.flush()

    def fileno(self):
        return self.stream.fileno()


class StderrCapture:
    def __init__(self, reader, output, limit=65536):
        self.reader = reader
        self.output = output
        self.limit = limit
        self.error = None
        self.thread = threading.Thread(target=self.drain, daemon=True)
        self.thread.start()

    def drain(self):
        remaining = self.limit
        try:
            while True:
                data = self.reader.read(4096)
                if not data:
                    break
                if remaining:
                    keep = data[:remaining]
                    self.output.write(keep)
                    remaining -= len(keep)
            self.output.flush()
        except BaseException as e:
            self.error = e
        finally:
            self.reader.close()

    def finish(self):
        self.thread.join(5)
        if self.thread.is_alive():
            raise RuntimeError('stderr pipe did not close')
        if self.error:
            raise self.error
