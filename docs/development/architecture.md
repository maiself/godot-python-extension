# Architecture

## Structure

This project can be thought as having three layers:

  - The lowest layer is written in C++ and implements the GDExtension. It's two main jobs are to provide a sparse minimal binding of the GDExtension API to Python, and to cast Godot's variant types to and from Python equivalents. No classes or methods are bound by this layer. It's code is located in [`src`](https://github.com/maiself/godot-python-extension/tree/master/src).

    This is the only layer written in C++, the remainder of the project is written entirely in Python.

  - The second layer uses the sparse GDExtension API bindings provided by the previous layer to implement the `godot` module. It's code can be found in [`lib/godot`](https://github.com/maiself/godot-python-extension/tree/master/lib/godot).

    Variant types are bound immediately, while all `Object` derived classes are bound automatically on demand.

  - The final layer uses the `godot` module provided by the previous layer to implement Python script support for use in the engine. It's code can be found in [`lib/godot/_python_extension`](https://github.com/maiself/godot-python-extension/tree/master/lib/godot/_python_extension).


