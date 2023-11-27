# Without building

When working exclusively on the Python portions of the extension (located under [`lib`](https://github.com/maiself/godot-python-extension/tree/master/lib)) it is possible to skip building of extension. This can help achieve faster iteration while developing, or even avoid the need to set up a build environment.

Releases and changes to C++ code will still require building the extension however.


## Mechanism

Setting the `GODOT_PYTHON_MODULE_LIB_DIR` environment variable will change where the `godot` module is loaded from.

When set to the path of the source [`lib`](https://github.com/maiself/godot-python-extension/tree/master/lib) directory, the `godot` module will be loaded from that directory instead of the embedded module archive.

For example, if the project's repository is checked out to `~/src/godot-python-extension` then starting the Godot editor may look like this:

```bash
GODOT_PYTHON_MODULE_LIB_DIR=~/src/godot-python-extension/lib godot -e
```


## Live reload

After modifying the `godot` module it is possible to reload portions of it without restarting the editor.

While in the editor press `Ctrl + Shift + P` to open the command palette. Then search for "`Reload Python Extension Modules`".

Only some modules are currently enabled for reloading, as module reloading comes with some caveats. See [`lib/godot/_python_extension/editor/__init__.py`](https://github.com/maiself/godot-python-extension/tree/master/lib/godot/_python_extension/editor/__init__.py) for the list of currently reloadable modules.

