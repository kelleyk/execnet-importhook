#!/usr/bin/env python3.5

import sys
import time
import importlib
import importlib.util


class ExecnetSourceLoader(importlib._bootstrap_external.SourceLoader):
    def __init__(self, source_path, source_bytes):
        self.source_path = source_path
        self.source_bytes = source_bytes

    # N.B.: We override this instead of just overriding get_filename() and get_source() in order to skip attempts at
    # reading or writing cached bytecode.
    def get_code(self, fullname):
        code_object = self.source_to_code(self.source_bytes, self.source_path)
        return code_object
        

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

        self.ch.send(fullname)
        result = self.ch.receive()
        
        if result is None:
            return None

        # TODO: Do any of the other arguments that ModuleSpec takes matter?
        return importlib._bootstrap.ModuleSpec(fullname, ExecnetSourceLoader(*result))

    def install(self):
        assert self not in sys.meta_path
        sys.meta_path.append(self)

        
if __name__ == '__channelexec__':
    ExecnetFinder(channel).install()
    channel.send('ready')
    while True:
        time.sleep(0)
