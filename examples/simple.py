import os
import os.path
import sys
import threading
from functools import partial

import pytest
import execnet

import execnet_importhook


exit_event = threading.Event()
ENDMARKER = object()

        
def execnet_slave_main(channel):
    channel.send('hello from the slave!')

    # Now, this wouldn't work if we skipped install_import_hook()!
    try:
        import baz
    except ImportError:
        channel.send('unable to import baz')
    else:
        # Should print 'baz.hello = world'.
        channel.send('baz.hello = {}'.format(baz.hello))

        
def execnet_master_main(install_hook=True, callback=None, gw=None, slave_main=execnet_slave_main):
    callback = callback or handle_ch
    exit_event.clear()  # to allow multiple test cases to run despite our gross global state

    # This directory contains the 'baz' module.  Adding it to sys.path means that 'baz' will be importable on the
    # master, but not (normally) on any of the slaves.
    baz_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../test/not-in-default-path')
    if baz_path not in sys.path:
        sys.path.append(baz_path)

    # Create another Python interpreter to be our slave.  (This could just as well be any other remote interpreter that
    # execnet supports.)
    gw = gw or execnet.makegateway()

    # This is all of the setup that we need to do!  This creates a channel to the gateway (and inserts itself into the
    # slave's import machinery) as well as a callback to service requests on this side.
    if install_hook:
        execnet_importhook.install_import_hook(gw)

    # Now we can go about our business.
    ch = gw.remote_exec(slave_main)
    ch.setcallback(partial(callback, ch), ENDMARKER)

    # When execnet_slave_main() finishes, our callback (handle_ch) will get ENDMARKER and set() the event, so that we
    # know to let the master end too.
    exit_event.wait()

        
def handle_ch(ch, item):
    """Callback that receives messages from the slave."""
    if item is ENDMARKER:
        return exit_event.set()
    print('received: {}'.format(item))


@pytest.mark.parametrize(('gw_spec',), [
    ('popen//python=python3.5',),
    ('popen//python=python3.4',),
    # ('popen//python=python3.3',),  # fails with 'ExecnetFinder' object has no attribute 'find_module()''
    # ('popen//python=python3.2',),  # fails with 'AttributeError: find_module()'
    # --
    # ('popen//python=python2.7',),  # has a completely different import system
])
class TestsImportHook(object):
    def _run(self, slave_main, install_hook=True, gw_spec=None):
        msgs = []
        
        def handler(ch, item):
            if item is ENDMARKER:
                return exit_event.set()
            msgs.append(item)

        gw = execnet.makegateway(gw_spec)
        execnet_master_main(install_hook=install_hook, callback=handler, slave_main=slave_main, gw=gw)
        return msgs
        
    def test_with_importhook(self, gw_spec):
        msgs = self._run(install_hook=True, slave_main=execnet_slave_main, gw_spec=gw_spec)
        assert msgs == [
            'hello from the slave!',
            'baz.hello = world',
        ]
        
    def test_without_importhook(self, gw_spec):
        msgs = self._run(install_hook=False, slave_main=execnet_slave_main, gw_spec=gw_spec)
        assert msgs == [
            'hello from the slave!',
            'unable to import baz',
        ]

    def test_subpackage(self, gw_spec):
        def slave_main(channel):
            import baz
            channel.send('ok')
            
        msgs = self._run(slave_main=slave_main, gw_spec=gw_spec)
        assert msgs == ['ok']

    def test_relative_import(self, gw_spec):
        def slave_main(channel):
            # The 'baz.slurp' module contains a relative import of 'baz.barf'.
            import baz.slurp
            channel.send('ok')
    
        msgs = self._run(slave_main=slave_main, gw_spec=gw_spec)
        assert msgs == ['ok']

    def test_zipimport(self, gw_spec):
        def slave_main(channel):
            # When you 'pip install' intensional, you get an egg (zip).
            import intensional
            channel.send('ok')
    
        msgs = self._run(slave_main=slave_main, gw_spec=gw_spec)
        assert msgs == ['ok']
        

if __name__ == '__main__':
    execnet_master_main()

