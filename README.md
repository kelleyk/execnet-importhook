# execnet-importhook

This library implements a mechanism that allows execnet slaves to import modules only installed on the master.  (In
keeping with that theme, this library itself only needs to be installed on the master.)

When an import is about to fail (because the module is not present on the slave), the slave asks the master if the
master can find the module.  If it can, the master sends the slave the module's source; the slave can then successfully
import it.

Right now this feature works with both absolute and relative imports.  It only works with pure-Python modules (not with
extension modules), though adding support for those (in situations where the master and the slave are similar enough to
be using the same extension modules) would probably not be hard.  It currently supports Python 3.4 and Python 3.5 on the
slave side.  Adding support for Python 2 is most likely possible; I would just have to spend some time remembering
exactly how the import machinery works there, since it is rather different.  (I'll probably wind up doing this
eventually.)

The current implementation doesn't change the source of execnet itself at all; there's just an extra call right after
you create the gateway.

## Supported versions of Python

- cpython only (others untested).

- Master: python3.5 (others untested).

- Slave: python3.5; python3.4.
  python3.3 and python3.2 known not to work; have not investigated.
  python2.7 doesn't work either; it has a totally different import system and will take some effort.

## Limitations and warnings

- Irritatingly, you can't import execnet itself through execnet_importhook.  execnet uses apipkg, a library that
  replaces the original module object loaded into sys.modules with something that has no `__spec__`.  This breaks stuff.

- If you use `gateway.remote_exec()` to execute a module, that module cannot use relative imports.  (When `execnet`
  moves the module to the remote interpreter, it doesn't set the package's name correctly, so Python will barf with
  `SystemError: Parent module '' not loaded, cannot perform relative import`.)

  However, if you import other modules from that module, and *those* modules (shipped to the remote interpreter by
  `execnet_importhook`) use relative imports, that will work just fine.

  This can be worked around by manually setting `__name__` and causing both that module and its parent to be imported and
  (I believe) placed in sys.modules, but that is probably not worth the trouble.

  (Internal notes:)
  In the remotely-executed module, `__name__ == '__channelexec__'` and `__package__` and `__path__` are undefined.
  See `_calc___package__()` for how the package name is calculated.  This winds up being '', which causes
  the above error.
