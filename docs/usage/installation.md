# Installation

This page describes several methods to install prebuilt versions of the extension. See [](/development/building.md) if your looking to build the extension from source.

```{note}
All instructions here assume you will be installing into a `addons/godot-python-extension` directory within your project.

Other installation locations are also possible, but please keep the original layout of all files within the installation, including all licenses, intact.
```


## From Godot's Asset Library

_godot-python is in early development and is not yet available on the Godot Asset Library._

## From GitHub releases

_godot-python is in early development and does not yet have an official release._

[//]: # (Visit the project's [releases page]&#40;https://github.com/maiself/godot-python-extension/releases&#41; and download the archive for the version of the extension you need. Then extract the archive into the `addons/godot-python-extension` directory within your project.)

## From nightly builds (GitHub Actions)

You can download nightly builds from [GitHub Actions](https://github.com/maiself/godot-python-extension/actions). Keep in mind nightly builds may be unstable and are not recommended for production setups. Right now, they are also not packaged like regular release builds, and may not be usable out of the box.

## As a git submodule

To install a prebuilt version of the extension from the [`prebuilt-releases`](https://github.com/maiself/godot-python-extension/tree/prebuilt-releases) branch as a submodule in `addons/godot-python-extension`:

```bash
# Add and checkout the submodule.
git submodule add --name godot-python-extension --branch prebuilt-releases \
	-- https://github.com/maiself/godot-python-extension addons/godot-python-extension

# Update the submodule.
git submodule update --init --remote -- godot-python-extension
```

To update the extension to a newer version run the submodule update command again.


## As a shallow submodule

It is possible to create a submodule using a shallow checkout of [`prebuilt-releases`](https://github.com/maiself/godot-python-extension/tree/prebuilt-releases) that contains only binaries from the version actually needed, rather than all versions in the branch history.

```{caution}
This method is more advanced than the others, and may not provide much benefit over a simple submodule as described in the [previous section](#as-a-git-submodule). A thorough understanding of Git's workings is strongly recommended if considering this method.
```

To initialize a shallow checkout of the [`prebuilt-releases`](https://github.com/maiself/godot-python-extension/tree/prebuilt-releases) branch as a submodule in `addons/godot-python-extension`:

```bash
# Add the submodule using a shallow checkout.
git submodule add --name godot-python-extension --depth 1 \
	-- https://github.com/maiself/godot-python-extension addons/godot-python-extension

# Add the `prebuilt-releases` branch to the submodule (as its not included by default).
git -C addons/godot-python-extension remote set-branches --add origin prebuilt-releases

# Set the submodule branch and mark it as shallow.
git config -f .gitmodules submodule.godot-python-extension.branch prebuilt-releases
git config -f .gitmodules submodule.godot-python-extension.shallow true
```

Then update the submodule:

```bash
# Update the module ensuring only a shallow checkout is performed.
git submodule update --init --remote --recommend-shallow --depth 1 \
	-- godot-python-extension

# Stage the changes to the submodule.
git add .gitmodules addons/godot-python-extension
```

The path `addons/godot-python-extension` can also be changed, but make sure to adjust each command above to use the same path. Clones of a repository making use of this method may need to repeat these steps.


