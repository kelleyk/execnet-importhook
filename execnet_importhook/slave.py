#!/usr/bin/env python3.5

import sys
PY2 = sys.version_info < (3,)

import time
import importlib
if PY2:
    pass
else:
    import importlib.util

if sys.version_info < (3, 5):  # 3.4
    importlib_SourceLoader = importlib._bootstrap.SourceLoader
else:  # 3.5
    importlib_SourceLoader = importlib._bootstrap_external.SourceLoader

    
class ExecnetSourceLoader(importlib_SourceLoader):
    def __init__(self, source_path, source_bytes):
        self.source_path = source_path
        self.source_bytes = source_bytes

    # N.B.: We override this instead of just overriding get_filename() and get_source() in order to skip attempts at
    # reading or writing cached bytecode.
    def get_code(self, fullname):
        code_object = self.source_to_code(self.source_bytes, self.source_path)
        return code_object

    # FileLoader provides get_filename() and get_data().  For some reason, we have trouble
    # using the 'traceback' module on the slave without these two functions implemented.
    # TODO: Add test coverage for the 'traceback' module on the slave.
    
    def get_filename(self, fullname):
        return self.source_path
    
    def get_data(self, path):
        return self.source_bytes
        

class ExecnetFinder(object):

    def __init__(self, ch):
        self.ch = ch

    def find_spec(self, fullname, path, target=None):
        # path and target may both be None.        
        # TODO: We ignore path and target at the moment.  What situations might they be useful/necessary in?
        
        # "If this is a top-level import, path will be None. Otherwise, this is a search for a subpackage or module and
        # path will be the value of __path__ from the parent package."
        # (@KK: That is, if we import foo.bar, path will be a single-item list containing the path to 'foo'.)
        
        # # (This will turn into a call back to the execnet master.)
        # result = get_source(fullname)

        self.ch.send((fullname, path, target))
        result = self.ch.receive()
        
        if result is None:
            return None
        
        # TODO: Do any of the other arguments that ModuleSpec takes matter?
        source_path, source_bytes, is_package = result
        loader = ExecnetSourceLoader(source_path, source_bytes)

        spec = importlib._bootstrap.ModuleSpec(fullname, loader, origin=source_path, is_package=is_package)
        spec.has_location = True  # XXX: constructor doesn't take this arg
        return spec

    def install(self):
        assert self not in sys.meta_path
        sys.meta_path.append(self)

        
if __name__ == '__channelexec__':
    if PY2:
        channel.send({'err': 'unsupported-python', 'version': sys.version_info})
    else:
        ExecnetFinder(channel).install()
        channel.send({'ready': True})
        while True:
            time.sleep(0)

        
