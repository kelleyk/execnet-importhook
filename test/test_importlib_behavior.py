import sys
import importlib.util


# TODO: Test with a namespace package.


class TestsFindSpecBehavior(object):
    # These tests depend on 'foo' and 'foo_pyc_only' being in sys.path.  Should probably wrap this up a bit more neatly.
    # They also require that 'tornado' be installed (to provide the native module).
    # Should also test with eggs.
    
    def test_nonexistant_module(self):
        spec = importlib.util.find_spec('nonexistant_module')
        assert spec is None

    def test_module_with_source(self):
        # TODO: explicitly test that this is true regardless of whether bytecode is present
        spec = importlib.util.find_spec('foo')
        assert isinstance(spec.loader, importlib._bootstrap_external.SourceFileLoader)

    def test_module_without_source(self):
        # e.g. bytecode-only
        spec = importlib.util.find_spec('foo_pyc_only')
        assert spec.loader is None
        
    def test_native_module(self):
        spec = importlib.util.find_spec('tornado.speedups')
        assert isinstance(spec.loader, importlib._bootstrap_external.ExtensionFileLoader)

    def test_builtin_module(self):
        # Any of the modules in this list will work.
        assert 'sys' in sys.builtin_module_names
        
        spec = importlib.util.find_spec('sys')
        assert spec.loader is importlib._bootstrap.BuiltinImporter

