# Qt Script Generator for Qt 6

This repository ports the Qt Labs Qt Script Generator to Qt 6. It generates
QtScript bindings from Qt headers and typesystem specifications, builds them as
script extension plugins, and provides `qs_eval` for running scripts. The Qt 6
port is tested on Windows with MSVC and Qt 6.8.3 and 6.12.1.

QtScript is not part of standard Qt 6. The build also requires the separate
[QtScript Qt 6 port](https://github.com/JulienMaille/qtscript-qt6).

## Bindings

The supported generated plugins are `qt.core`, `qt.gui`, `qt.widgets`,
`qt.network`, `qt.sql`, `qt.xml`, `qt.printsupport`, `qt.uitools`, and `qt.svg`.
The Qt 5 multimedia, OpenGL and XML Patterns binding projects are not part of
this Qt 6 build. Not every Qt API can be represented by the generator; see
`generator/AUDIT-qt6.md` and the rejection logs for details.

## Requirements

- Windows, a 64-bit MSVC toolchain and PowerShell.
- Qt 6.8.3 or 6.12.1 with the modules listed in `CMakeLists.txt`, including
  the separately built QtScript and QtScriptTools libraries.
- CMake 3.25 or newer, Ninja, qmake and nmake.

Build and install the QtScript port first, following its instructions. Set
`$Qt` below to the Qt installation prefix and `$QtScript` to the prefix
containing the installed QtScript libraries. If QtScript is installed into the
Qt prefix, both can point to the same directory.

## Build and test

From a PowerShell prompt at the repository root:

```powershell
$Qt = 'C:\Qt\6.8.3\msvc2022_64'
$QtScript = $Qt # Change this if QtScript is installed separately.

.\generator\build-generator.ps1 -QtPrefix $Qt -Configuration Release
.\generator\regen-all.ps1 -QtPrefix $Qt -ApplyCurated -PublishRoot $PWD.Path
.\build.ps1 -QtPrefix $Qt -QtScriptPrefix $QtScript -Configuration Release
.\test.ps1 -QtPrefix $Qt -QtScriptPrefix $QtScript -Configuration Release
```

The regeneration command **cleans `regen-test/` and replaces
`generated_cpp/`** by default. Do not point its output or publish options at
directories containing files you need to preserve. The build puts plugins in
`plugins/script/` and the Release evaluator in
`qtbindings/qs_eval/release/qs_eval.exe`. The test script uses an offscreen Qt
platform and writes logs under `logs/`.

To run an example interactively, ensure the Qt and QtScript `bin` directories
are on `PATH`, then run, for example:

```powershell
$env:PATH = "$QtScript\bin;$Qt\bin;$env:PATH"
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
Push-Location examples
..\qtbindings\qs_eval\release\qs_eval.exe CollidingMice.js
Pop-Location
```

## Generation and maintenance

The pipeline is Qt headers and `generator/typesystem_*.xml` → generator →
`generated_cpp/` → binding plugins → QtScript. Typesystem files specify the
exposed classes and members, modifications and module dependencies. Change the
typesystem or generator source rather than editing generated output.

`generated_cpp/` is ignored by Git. Run the regeneration step explicitly
before building after changing the generator, typesystems, or Qt version; the
build script does not regenerate it. The
hand-maintained sources in `generator/curated/` are deliberately reapplied by
`-ApplyCurated`; they are not disposable generated output. Generated `jsx/`
API descriptions are also ignored and are not build inputs.

CI regenerates all nine modules, checks the per-version surface contract and
reject budget, builds the plugins and runs the smoke and generated tests. To
run the same pre-build checks locally after regeneration:

```powershell
# Use surface-contract-qt683.json for Qt 6.8.3; the default is for Qt 6.12.
.\tools\surface-contract.ps1 -GeneratedRoot .\generated_cpp -Contract .\generator\surface-contract-qt683.json
.\tools\reject-budget.ps1 -LogRoot .\regen-test\logs
```

The surface, enum-value and construction tests run by default in `test.ps1`;
their `-SkipSurfaceCoverage`, `-SkipEnumValues` and `-SkipConstructionSweep`
switches are intended for shorter local iterations, not full verification.
See the workflows in `.github/workflows/` for the complete CI recipes.

## License

See `LICENSE.LGPL`, `LGPL_EXCEPTION.txt` and `LICENSE.PREVIEW.COMMERCIAL` for
the license terms and exceptions included with the original project.
