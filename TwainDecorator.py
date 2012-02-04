from cStringIO import StringIO
import Image
import logging

from imagescanner.backends import base, twain
from imagescanner.backends.twain import twain as _twain

class ScannerManager(base.ScannerManager):
    def __init__(self, **kwargs):
        logging.debug('Creating TwainDecorator.ScannerManager')
        base.ScannerManager.__init__(self, **kwargs)

    def _refresh(self):
        self._devices = []
        src_manager = _twain.SourceManager(0)
        devices = src_manager.GetSourceList()
        for dev in devices:
            scanner_id = 'twain-%s' % len(self._devices)
            try:
                scanner = Scanner(scanner_id, dev)
                self._devices.append(scanner)
            except Exception, exc:
                logging.debug(exc)
        src_manager.destroy()

class Scanner(twain.Scanner):
    def __init__(self, scanner_id, source_name):
        logging.debug('Creating TwainDecorator.Scanner')
        twain.Scanner.__init__(self, scanner_id, source_name)
        self._scan_before_callbacks = []
   
    def scan(self, dpi=200):
        self._open()
        self.on_scan_before(self._scanner)
        self._scanner.RequestAcquire(0, 0)
        info = self._scanner.GetImageInfo()
        if info:
            (handle, more_to_come) = self._scanner.XferImageNatively()
            str_image = _twain.DIBToBMFile(handle)
            _twain.GlobalHandleFree(handle)
            self._close()
            return Image.open(StringIO(str_image))

        self._close()
        return None
    
    def on_scan_before(self, scanner):
        for callback in self._scan_before_callbacks:
            if callback and hasattr(callback, '__call__'):
                callback(scanner)
