# -*- coding: utf-8; -*-

import sys
import importlib
import importlib.util
import zipimport
from functools import partial

if sys.version_info < (3, 5):  # 3.4
    importlib_SourceFileLoader = importlib._bootstrap.SourceFileLoader
else:  # 3.5
    importlib_SourceFileLoader = importlib._bootstrap_external.SourceFileLoader

ENDMARKER = object()


def get_source(fullname, package=None):
    # find_spec() takes an optional argument named 'package' that is used to resolve relative imports.  It's not
    # necessary if the module name is absolute.
    spec = importlib.util.find_spec(fullname)

    print('** get_source(fullname={})'.format(fullname))
    
    if spec is None or spec.loader is None:
        return None

    if isinstance(spec.loader, (
            importlib._bootstrap_external.SourceFileLoader,
            zipimport.zipimporter,
    )):
        source_path = spec.loader.get_filename(fullname)
        source_bytes = spec.loader.get_data(source_path)
        is_package = loader_is_package(spec.loader, fullname)
        return (source_path, source_bytes, is_package)
        
    print('** unable to provide import \'{}\' to slave: spec.loader={}'.format(
        fullname,
        None if spec is None else spec.loader))
    import pdb; pdb.set_trace()
    return None



def loader_is_package(loader, name):
    # Excerpt from importlib._bootstrap.spec_from_loader().

    if hasattr(loader, 'is_package'):
        try:
            is_package = loader.is_package(name)
        except ImportError:
            is_package = None  # aka, undefined
    else:
        # the default
        is_package = False

    return is_package


def handle_import_ch(ch, item):
    if item is ENDMARKER:
        return
    
    fullname, path, target = item
    
    try:
        result = get_source(fullname)
    except:
        raise
    else:
        ch.send(result)


def install_import_hook(gateway):
    from . import slave as importhook_slave
    import_ch = gateway.remote_exec(importhook_slave)

    # Avoid a race in setting up the hook on the remote (slave) side by waiting for it to confirm that it's ready.
    status = import_ch.receive()
    if 'err' in status:
        raise RuntimeError('Slave reported error during setup: {} ({})'.format(
            status['err'], {k: v for k, v in status.items() if k != 'err'}))
    elif status != {'ready': True}:
        raise ValueError('Unexpected response from slave.')
    
    import_ch.setcallback(partial(handle_import_ch, import_ch), ENDMARKER)
