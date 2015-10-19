#!/usr/bin/env python3.5

import importlib
import importlib.util


def get_source(fullname, package=None):
    
    # find_spec() takes an optional argument named 'package' that is used to resolve relative imports.  It's not
    # necessary if the module name is absolute.
    spec = importlib.util.find_spec(fullname)

    if spec is None or spec.loader is None or \
       not isinstance(spec.loader, importlib._bootstrap_external.SourceFileLoader):
        return None

    source_path = spec.loader.get_filename()
    source_bytes = spec.loader.get_data(source_path)
    return (source_path, source_bytes)


class ExecnetSourceLoader(importlib._bootstrap_external.SourceLoader):
    def __init__(self, source_path, source_bytes):
        self.source_path = source_path
        self.source_bytes = source_bytes

    # N.B.: We override this instead of just overriding get_filename() and get_source() in order to skip attempts at
    # reading or writing cached bytecode.
    def get_code(self, fullname):
        code_object = self.source_to_code(self.source_bytes, self.source_path)
        return code_object
        

# @KK: This version adds '_FOO_FLAG', which just prevents recursion so that we can test this without execnet.
class ExecnetFinder(object):
    _FOO_FLAG = False

    def find_spec(self, fullname, path, target=None):
        # path and target may both be None.        
        # TODO: We ignore path and target at the moment.  What situations might they be useful/necessary in?
        
        # "If this is a top-level import, path will be None. Otherwise, this is a search for a subpackage or module and
        # path will be the value of __path__ from the parent package."
        # (@KK: That is, if we import foo.bar, path will be a single-item list containing the path to 'foo'.)

        if ExecnetFinder._FOO_FLAG:
            return None
        
        ExecnetFinder._FOO_FLAG = True
        # (This will turn into a call back to the execnet master.)
        result = get_source(fullname)
        ExecnetFinder._FOO_FLAG = False
        
        if result is None:
            print('** ExecnetFinder: unable to find')
            return None

        print('** ExecnetFinder: returning result')
        # TODO: Do any of the other arguments that ModuleSpec takes matter?
        return importlib._bootstrap.ModuleSpec(fullname, ExecnetSourceLoader(*result))
 

def test_find_and_load():
    import sys
    #sys.meta_path.append(ExecnetFinder())
    sys.meta_path = [ExecnetFinder()] + sys.meta_path

    import foo
    #import derplib

    assert foo.hello == 'world'
    

if __name__ == '__main__':
    test_find_and_load()
    
