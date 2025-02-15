# Platforms

The following is godot-python's current state of support for various platforms and architectures:

```{csv-table}
:delim: "|"
:header: "Platform | Architecture | Local Development | Export / Deployment | PyPi Packages / Pip"

🐧️ Linux   | x86_64 | ✅   | ✅❔ | 📐
🐧️ Linux   | x86_32 | ❌   | ❌   | 
🐧️ Linux   | arm64  |      |      | 
🐧️ Linux   | arm32  |      |      | 
🪟️ Windows | x86_64 | ✅   | ✅❔ | 📐
🪟️ Windows | x86_32 | ❌   | ❌   | 
🪟️ Windows | arm64  |      |      | 
🪟️ Windows | arm32  | ❌   | ❌   | 
🍎️ macOS   | x86_64 | ✅   | ✅❔ | 📐
🍎️ macOS   | arm64  | ✅❔ | ✅❔ | 📐
🤖️ Android | x86_64 |      |      | 
🤖️ Android | x86_32 |      |      | 
🤖️ Android | arm64  |      | 📐   | 📐❔
🤖️ Android | arm32  |      |      | 
🍏️ iOS     | x86_64 |      |      | 
🍏️ iOS     | arm64  |      |      | 
🌐️ Web     | wasm64 |      | ❔   | 
🌐️ Web     | wasm32 |      | 📐   | 📐❔
```

```{csv-table} Key
:delim: "-"

✅ - Supported
✅❔ - Support implemented or intended but may need testing
📐 - Support planned or in progress
📐❔ - Unsure if support is possible or will be implemented
❌ - No support planned or support not possible for platform
```
