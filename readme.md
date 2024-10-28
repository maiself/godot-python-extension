# godot-python-extension

> [!WARNING]  
>
> This repository is a work in progress and should be considered experimental. It is not production ready.
>
> Please use version control with any project.

This repository provides [**Python**](https://www.python.org/) language bindings for the [**Godot**](https://godotengine.org/) game engine.

The bindings are implemented as a [GDExtension](https://godotengine.org/article/introducing-gd-extensions) that exposes Godot's APIs and enables extension classes and scripts to be written in Python.


## Structure

This project can be thought as having three layers:

  - The lowest layer is written in C++ and implements the GDExtension. It's two main jobs are to provide a sparse minimal binding of the GDExtension API to Python, and to cast Godot's variant types to and from Python equivalents. No classes or methods are bound by this layer. It's code is located in [`src/`](src/).

    This is the only layer written in C++, the remainder of the project is written entirely in Python.

  - The second layer uses the sparse GDExtension API bindings provided by the previous layer to implement the `godot` module. It's code can be found in [`lib/godot/`](lib/godot/).

    Variant types are bound immediately, while all `Object` derived classes are bound automatically on demand.

  - The final layer uses the `godot` module provided by the previous layer to implement Python script support for use in the engine. It's code can be found in [`lib/godot/_python_extension/`](lib/godot/_python_extension/).


## Building

> [!NOTE]
>
> Godot version 4.2 or later is required to build and load this extension.

To clone and initialize the repository:
```sh
git clone https://github.com/maiself/godot-python-extension.git
cd godot-python-extension
git submodule update --init
```

To build run from the project root:
```sh
scons godot=<PATH_TO_GODOT_BINARY>
```

The path to the `godot` binary is needed to extract the `gdextension_interface.h` and `extension_api.json` files from the engine. The built extension shared object will be placed in `bin/`.

> [!NOTE]
>
> Currently this project has only been tested on Linux with Python versions 3.11 and 3.12. Modifications to the [SConstruct](SConstruct) file may be needed for other platform configurations. Please submit issues and pull requests for any problems you run into.


## Development

The main parts are functional, but much is still in progress.

The `godot` module has the same API layout and stability for everything provided by Godot itself, but Python specific interfaces may still need adjusting.

Currently the system installed Python is used, but embedded and isolated build should be easy to add.

Many **_`XXX:`_** comments are present, most of which currently lack a description. These are marking potential defects in the code: bugs, hacks, partial implementations, or things to check for correctness; and should be documented, fixed and removed when possible.

Documentation on development and use needs to be expanded on.

**Contributions of any kind are highly welcomed!**


