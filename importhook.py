#!/usr/bin/env python3.5

import time
import importlib
import importlib.util
from functools import partial
    
import execnet


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


ENDMARKER = object()


def execnet_master_main():
    gw = execnet.makegateway()

    import importhook_slave
    import_ch = gw.remote_exec(importhook_slave)
    data = import_ch.receive()
    assert data == 'ready'
    import_ch.setcallback(partial(handle_import_ch, import_ch), ENDMARKER)
    
    ch = gw.remote_exec(execnet_slave_main)
    ch.setcallback(partial(handle_ch, ch), ENDMARKER)

    while True:
        time.sleep(0)

        
def handle_ch(ch, item):
    if item is ENDMARKER:
        print('ch ENDS')
        return
    
    print('got from ch: {}'.format(item))
    
    
def handle_import_ch(ch, item):
    if item is ENDMARKER:
        print('import_ch ENDS')
        return
    
    print('import_ch got item: {}'.format(item))
        
    try:
        result = get_source(item)
    except:
        raise
    else:
        print('sending result; is none? {}'.format(result is None))
        ch.send(result)

        
def execnet_slave_main(channel):
    channel.send('hello from slave_main')
    import sys
    sys.path = []
    import baz
    channel.send('baz.hello = {}'.format(baz.hello))


if __name__ == '__main__':
    import sys
    import os
    import os.path
    sys.path.append(os.path.join(os.getcwd(), 'not-in-default-path'))
    
    execnet_master_main()
    
