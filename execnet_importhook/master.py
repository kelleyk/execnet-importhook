# -*- coding: utf-8; -*-

import time
import importlib
import importlib.util
from functools import partial

ENDMARKER = object()


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


def handle_import_ch(ch, item):
    if item is ENDMARKER:
        # print('import_ch ENDS')
        return
    
    # print('import_ch got item: {}'.format(item))
        
    try:
        result = get_source(item)
    except:
        raise
    else:
        # print('sending result; is none? {}'.format(result is None))
        ch.send(result)


def install_import_hook(gateway):
    from . import slave as importhook_slave
    import_ch = gateway.remote_exec(importhook_slave)

    # Avoid a race in setting up the hook on the remote (slave) side by waiting for it to confirm that it's ready.
    data = import_ch.receive()
    assert data == 'ready'
    
    import_ch.setcallback(partial(handle_import_ch, import_ch), ENDMARKER)