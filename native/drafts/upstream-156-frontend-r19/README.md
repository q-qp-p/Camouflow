# Glint R19: checkpoint frontend corrections

**47 C++ frontend units passed. Registered for explicit build/test; not linked, selected or runtime-admitted.**

| Gate | Result |
| --- | --- |
| Complete source recipe | 180 unchanged R18 patches + one compatibility patch |
| Indexed apply / reverse | 181 / 181; 511 final files, 353 upstream originals restored |
| Checkpoint declarations | All 337 retained across seven binaries |
| C++ frontend | 47/47 units, including all 30 checkpoint case-source files; no timeouts |
| Chromium style / modules | Original checks retained; original invalid-callback negative control reproduced |
| Link / native tests / browser runtime | Pending |
| Production / package admission | Not admitted |

## Changes

- Document and service-worker callbacks use stateless functors with explicitly
  bound arguments. Weak ownership, ticket validation, deadlines and once-only
  completion are retained.
- Worker lifecycle checks explicitly select `ExecutionContext::IsContextDestroyed`.
- Browser checkpoint tests use Chromium 156's `BrowserWindowInterface::GetProfile`.
- The isolated frontend harness generated shared Mojom code without a variant
  typemap, matching `mojom.gni`, and supplied missing upstream Blink test bindings.
  Generated files are not patched or shipped in this recipe.

[Frontend receipt](frontend-validation.json) records the measured scope.
[Source preparation](preparation.json) covers application and reversal;
[native plan](native-case-plan.json) lists declarations, not executed tests.

The source-bound crash controller, fresh PRE/post profiles, native discovery,
existing privacy regressions and independent runtime verification remain required.
R16 selection and rollback runtimes are unchanged. This does not establish an
atomic whole-profile snapshot, power-loss durability or external-detector results.

## Explicit build/test entry points

```powershell
python scripts/native_build.py preflight --workspace D:\Glint156Candidate --candidate upstream-156-frontend-r19
```

After guarded source preparation and a successful candidate-bound browser build:

```powershell
python scripts/verify_native_checkpoint_units.py --workspace D:\Glint156Candidate --candidate upstream-156-frontend-r19 --jobs 4 --report-dir D:\GlintManagerQA\r19-native-run
```

The report directory must be new. Resource, selected-source, SDK and build-receipt
checks remain mandatory. Browser dispatch separates 20 completed browser gtests
from one qualified intentional crash; a forced exit is never counted as PASS.
Registration does not change the selected source or certify a native execution.
The preparation receipt records the earlier, unregistered staging state.
