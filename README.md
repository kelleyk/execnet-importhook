# Supported versions of Python

- cpython only (others untested).

- Master: python3.5 (others untested).

- Slave: python3.5; python3.4.
  python3.3 and python3.2 known not to work; have not investigated.
  python2.7 doesn't work either; it has a totally different import system and will take some effort.

# Limitations and warnings

- Only tested with cpython.  Only tested with Python 3.5.  Definitely does not support Python 2.x right now.

  The implementation is built on `importlib`, which barely exists in Python 2.7.  Support is probably possible, but
  would take some tinkering.

- If you use `gateway.remote_exec()` to execute a module, that module cannot use relative imports.  (When `execnet`
  moves the module to the remote interpreter, it doesn't set the package's name correctly, so Python will barf with
  `SystemError: Parent module '' not loaded, cannot perform relative import`.)

  However, if you import other modules from that module, and *those* modules (shipped to the remote interpreter by
  `execnet_importhook`) use relative imports, that will work just fine.

  This can be worked around by manually setting __name__ and causing both that module and its parent to be imported and
  (I believe) placed in sys.modules, but that is probably not worth the trouble.

  (Internal notes:)
  In the remotely-executed module, __name__ == '__channelexec__' and __package__ and __path__ are undefined.
  See _calc___package__() for how the package name is calculated.  This winds up being '', which causes
  the above error.
