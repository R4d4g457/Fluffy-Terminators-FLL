
# SPIKE Prime Python Stub Development Report

**Version:** v12  
**Date:** November 2025  
**Author:** Fluffy Terminators FLL Team  

---

## 1  Purpose  

This document explains how the team generated and refined its custom Python type-stub package (`spike_stubs/`) for the **LEGO Education SPIKE Prime** MicroPython API and how to integrate it with **VS Code** using **Peter Staev’s LEGO SPIKE Prime / Mindstorms extension**.

The goals were to:  

- Enable full **IntelliSense**, hover help, and static type checking in VS Code.  
- Ensure compatibility with the **SPIKE 3 MicroPython runtime** on the hub.  
- Provide one-click **upload and run** functionality directly from VS Code.

---

## 2  Background  

When editing SPIKE Prime programs in VS Code, imports such as:

```python
import motor
import force_sensor
from hub import port
```

typically raise unresolved import warnings because these modules only exist within the hub firmware.

No official or community stubs covered the 2023–2025 SPIKE 3 API.  
We therefore built a complete set of **custom type stubs** and iteratively refined them through twelve versions, integrating them with the VS Code extension for upload and execution.

---

## 3  Development Summary  

| Version | Focus | Key Changes |
|:--:|:--|:--|
| **v1–v2** | Baseline | Added core modules (`motor`, `sensor`, `hub`, `app`). Minimal signatures. |
| **v3** | MicroPython compatibility | Added `ujson`, `uos`, `utime`, `ustruct`, etc. |
| **v4–v5** | Documentation coverage | Restored and expanded function-level docstrings. |
| **v6–v7** | API accuracy | Fixed constants and parameter orders; added `app.music` methods. |
| **v8–v9** | Completeness | Merged SPIKE + MicroPython API shapes; added `play_instrument()`. |
| **v10–v11** | Display and system modules | Added `color_matrix`, `device`, `runloop`, and fully documented `time`, `utime`, and `hub`. |
| **v12** | Final polish | Restored `time.localtime()` / `mktime()` and added `IMAGE_*` constants to `hub.light_matrix`. |

---

## 4  Data Sources and Verification  

- **Official LEGO SPIKE Prime Python Help**  
  <https://spike.legoeducation.com/prime/modal/help/lls-help-python>  
- **LEGO Education Lesson Plans**  
  <https://education.lego.com/en-au/lessons/?products=SPIKE%E2%84%A2+Prime+with+Python>  
- On-hub introspection via `dir()` and `help()` on modules.  
- **MicroPython standard library** documentation:  
  <https://micropython-stubs.readthedocs.io>  

---

## 5  Folder Structure  

```
Fluffy-Terminators-FLL/
│
├── spike_stubs/
│   ├── app.pyi
│   ├── color.pyi
│   ├── color_matrix.pyi
│   ├── device.pyi
│   ├── hub.pyi
│   ├── motor.pyi
│   ├── motor_pair.pyi
│   ├── time.pyi
│   ├── utime.pyi
│   ├── ujson.pyi
│   ├── uos.pyi
│   ├── urandom.pyi
│   ├── ustruct.pyi
│   ├── wait.pyi
│   └── …
└── .vscode/settings.json
```

---

## 6  VS Code Integration with Peter Staev’s Extension  

### 6.1  Install  

Search **“LEGO SPIKE Prime / Mindstorms VS Code Extension”** by **Peter Staev** in the Marketplace,  
or install manually:

```bash
code --install-extension PeterStaev.lego-spikeprime-mindstorms-vscode
```

🔗 GitHub: [https://github.com/PeterStaev/lego-spikeprime-mindstorms-vscode](https://github.com/PeterStaev/lego-spikeprime-mindstorms-vscode)

The extension enables:

- Direct Bluetooth or USB upload.  
- “Upload and Run on Hub” and “Stop Program” commands.  
- Serial log output from the hub.  

---

### 6.2  Project Setup  

Use the following VS Code settings:

```jsonc
{
  // --- Python analysis ---
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic",

  // Tell Pylance where your *.pyi stubs live:
  "python.analysis.stubPath": "./spike_stubs",

  // Include them for import resolution:
  "python.analysis.extraPaths": ["./spike_stubs"],

  // Silence “no module source” warnings for stub-only modules:
  "python.analysis.diagnosticSeverityOverrides": {
    "reportMissingModuleSource": "none"
  },

  // --- LEGO SPIKE extension settings ---
  "legoSpikePrime.hubType": "SPIKE3",     // or "SPIKE2", "Inventor"
  "legoSpikePrime.uploadMethod": "BLE",   // or "USB"
  "legoSpikePrime.pythonFilePattern": "**/*.py",
  "legoSpikePrime.autoConnect": true      // Auto-connect on VS Code start
}
```

**Explanation:**

- `stubPath` and `extraPaths` make Pylance aware of your stubs.  
- `diagnosticSeverityOverrides` hides spurious missing-module warnings.  
- `legoSpikePrime.*` entries configure the upload method and hub type.

---

### 6.3  Using the Extension  

1. Connect your SPIKE hub via USB or Bluetooth.  
2. Open your `.py` file and press `Ctrl + Shift + P` →  
   **SPIKE Prime: Upload and Run on Hub**.  
3. The extension handles uploading and automatically executes the program.  
4. Use **SPIKE Prime: Stop Program** or **SPIKE Prime: Show Logs** for debugging output.

---

## 7  Using the `# LEGO slot:X autostart` Directive  

> **Important:** This feature is **provided by the VS Code extension**, not by the SPIKE firmware itself.

You can control where and how your Python file is uploaded using a special comment header recognized by the **Peter Staev extension**:

```python
# LEGO slot:1 autostart

from hub import light_matrix
light_matrix.write("Hi!")
```

**Explanation:**

- `slot:1` → tells the extension to upload this file to **hub slot 1**.
- `autostart` → instructs the extension to **run the program immediately after upload**.  
- These directives are **parsed by the extension** before upload; they have **no effect** if you deploy code using the official LEGO Education app or other methods.

This is useful in competition or classroom environments for one-command *upload + run* behavior directly from VS Code.

For full documentation, see the extension README:  
<https://github.com/PeterStaev/lego-spikeprime-mindstorms-vscode#automatic-uploadstart-of-a-python-file>

---

## 8  Alternative Stub Sources  

| Source | Purpose | Use Case |
|:--|:--|:--|
| [pyhub-stubs](https://github.com/XenseEducation/pyhub-stubs) | SPIKE 2 / Mindstorms API coverage | Legacy projects |
| [SPIKEPythonDocs](https://github.com/tuftsceeo/SPIKEPythonDocs) | Full HTML reference | Docstring verification |
| [MicroPython-Stubs](https://micropython-stubs.readthedocs.io) | Standard library coverage | `u*` modules and `time` |

---

## 9  Outcome  

By **v12**, combined with the VS Code extension:

- All SPIKE 3 modules load cleanly under Pylance.  
- IntelliSense and hover help provide full documentation.  
- Upload and execution work directly from VS Code.  
- `# LEGO slot:X autostart` simplifies deployment control.  
- The setup is fully cross-platform (macOS, Windows, Linux).  

---
