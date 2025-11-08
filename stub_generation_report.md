
# SPIKE Prime Python Stub Development Report

**Version:** v12  
**Date:** November 2025  
**Author:** Fluffy Terminators FLL team  

---

## 1. Purpose  

This document explains how we generated and refined our custom Python type-stub package (`spike_stubs/`) for the **LEGO Education SPIKE Prime** MicroPython API.  
The goal was to provide full **editor IntelliSense, hover help, and type checking** within **VS Code**, while running code that matches the **on-hub SPIKE 3 Python runtime** (as documented at [spike.legoeducation.com/prime/modal/help/lls-help-python](https://spike.legoeducation.com/prime/modal/help/lls-help-python)).

---

## 2. Background  

When editing SPIKE Prime programs in VS Code, imports such as:

```python
import motor
import force_sensor
from hub import port
```

produce unresolved-import warnings because these modules only exist on the SPIKE hub’s MicroPython runtime.

No authoritative stub set existed for the current SPIKE 3 API (2023-2025 releases).  
Community stubs such as `pyhub-stubs` cover earlier SPIKE 2 or Mindstorms APIs but lack modules like `color_matrix`, `app.music`, and `runloop`.

Therefore, we created a custom stub collection and incrementally refined it through twelve iterations.

---

## 3. Development Process Summary  

| Version | Focus | Key Changes |
|----------|-------|-------------|
| **v1 – v2** | Initial baseline | Added core module stubs (`motor`, `sensor`, `hub`, `app`). Minimal signatures, no docstrings. |
| **v3** | Added MicroPython compatibility | Introduced `ujson`, `uos`, `utime`, `ustruct`, etc., so standard imports wouldn’t break. |
| **v4** | Restored lost per-function docs | Merged back docstrings for `distance_sensor`, `wait`, `app`, and sensor APIs after regression. |
| **v5** | Completed documentation coverage | Ensured `motor`, `motor_pair`, `light`, `status_light`, `timer`, and all `u*` modules had descriptive docstrings. |
| **v6** | Verified integer vs string constants | Corrected `color.RED = 1` etc. to match official SPIKE 3 docs. Added `orientation` constants. |
| **v7** | Corrected API shape | Fixed `hub.motion_sensor.tilt_angles()` return type, parameter order in `motor_pair.move_for_degrees`, and added `app.music.play_note`, `play_drum`, `set_tempo`, `get_tempo`, `stop`. |
| **v8** | Restored doc coverage after restructuring | Re-added rich docstrings to every callable; unified SPIKE 3 and MicroPython modules. |
| **v9** | Added new music API | Introduced `app.music.play_instrument()` with docstring and verified async signatures. |
| **v10** | Added display peripherals | Created full `color_matrix.pyi`, `device.pyi`, `runloop.pyi` with detailed documentation. |
| **v11** | Completed `time` and `hub` modules | Added comprehensive docstrings for `time`, `utime`, and all submodules of `hub` (button, light, light_matrix, motion_sensor, sound). |
| **v12** | Final polish | Restored `time.localtime()`, `time.mktime()`; added all built-in `IMAGE_*` constants (`IMAGE_CONFUSED`, `IMAGE_ANGRY`, etc.) to `hub.light_matrix`. |

---

## 4. Data Sources and Verification  

The stub content was cross-checked against:

- The **official LEGO SPIKE Prime Python help** site  
  → <https://spike.legoeducation.com/prime/modal/help/lls-help-python>
- Examples and tutorials from **LEGO Education Lesson Plans**  
  → <https://education.lego.com/en-au/lessons/?products=SPIKE%E2%84%A2+Prime+with+Python>
- On-hub introspection (where available) using `dir()` and `help()` on modules.
- Comparison with **MicroPython standard library** stubs from  
  <https://micropython-stubs.readthedocs.io>

---

## 5. Folder Structure  

```
Fluffy-Terminators-FLL/
│
├── spike_stubs/
│   ├── __init__.pyi
│   ├── app.pyi
│   ├── color.pyi
│   ├── color_matrix.pyi
│   ├── color_sensor.pyi
│   ├── device.pyi
│   ├── distance_sensor.pyi
│   ├── force_sensor.pyi
│   ├── hub.pyi
│   ├── light.pyi
│   ├── motor.pyi
│   ├── motor_pair.pyi
│   ├── runloop.pyi
│   ├── speaker.pyi
│   ├── status_light.pyi
│   ├── time.pyi
│   ├── utime.pyi
│   ├── ujson.pyi
│   ├── uos.pyi
│   ├── urandom.pyi
│   ├── ustruct.pyi
│   ├── wait.pyi
│   └── (other MicroPython shims)
└── .vscode/settings.json  ←  adds “spike_stubs” to `python.analysis.extraPaths`
```

---

## 6. Usage in VS Code  

```jsonc
// .vscode/settings.json
{
  "python.analysis.extraPaths": [
    "./spike_stubs"
  ],
  "python.analysis.autoSearchPaths": false,
  "python.analysis.typeCheckingMode": "basic",
  "python.languageServer": "Pylance"
}
```

Reload VS Code and IntelliSense will recognize `import motor`, `from hub import port`, etc., with hover documentation drawn from these stubs.

---

## 7. Alternative and Future Sources  

While these custom stubs were necessary for SPIKE 3’s undocumented API, developers may also use:

- **[pyhub-stubs](https://github.com/XenseEducation/pyhub-stubs)** – official SPIKE 2/Mindstorms stubs.
- **[SPIKEPythonDocs](https://github.com/tuftsceeo/SPIKEPythonDocs)** – auto-generated HTML reference.
- **[MicroPython-Stubs](https://micropython-stubs.readthedocs.io)** – for standard library coverage.

Future work could merge these sources to create a more authoritative, single-source stub distribution for SPIKE 3.

---

## 8. Outcome  

By v12:

- All modules compile cleanly under Pylance.  
- Every SPIKE API symbol has a stub and a docstring.  
- IntelliSense and hover help match official behavior.  
- MicroPython-standard modules are included to avoid import errors.  

These stubs now provide a **complete offline development environment** for SPIKE Prime Python programs on macOS/VS Code.

---
