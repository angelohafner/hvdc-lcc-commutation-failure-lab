# Publication audit - 16 November 2026

The owner requested an independent audit, application of its recommendations and public GitHub publication. This supersedes the earlier local-only instruction.

## Findings and applied recommendations

| Severity | Finding | Resolution and evidence |
|---|---|---|
| Important | Returned outgoing current with contradictory valve voltage could fall through into a successful classification | Return inconclusive immediately. The synthetic regression failed before the fix and passed afterward. Gamma/completion remain unavailable. All 3,805 current event objects are reproduced exactly. |
| Important | Whole-record source residual medians could hide a wrong short disturbance | Require independent AC-phase and DC residual checks in each of 97 profile segments. Regressions removing the CF-02 sag and CF-08 DC step failed before the fix and pass afterward. All original segments pass; maximum median AC/DC residuals are 182.757/1.545 V against the existing 1,000 V tolerance. |
| Minor | Guide described threshold crossing as the end of overlap | Explain that reverse-voltage evidence confirms extinction; a threshold crossing alone does not establish completion. |
| Publication | An early local Git blob contains a Windows-account creator stamp | Preserve original local commits and a Git bundle. Publish a new audited snapshot without those ancestors; scan all blobs reachable from the public branch. Native executed archives remain untouched. |
| Reproducibility | Verification depended on manual release checks | Add a Windows GitHub Actions workflow for Python, release content and all browser checks; pin the optional Playwright test dependency. CI is source-only and explicitly skips native-evidence tests. |
| Publication | Pages, package and documentation still described publication as deferred | Add source/download links, refresh report and offline package, and record actual deployment checks below. |

## Independent evidence

The read-only reviewer verified all 31 archived project/output hashes, timing, SI units and exact raw-to-float64 NPZ values. It independently reproduced 1,423 normal, 153 reduced-margin, 669 unsuccessful-transfer, two resumed-conduction and 1,558 inconclusive attempts. Both resumed-conduction examples have no outgoing gate command in their inspected interval. All 29 browser recordings match native-derived float32 values exactly: 1,270,029 sample times and 43,180,986 signal values.

## Verification

- 22 local Python tests passed, including three new failing-then-passing regressions.
- Engineering audit: 31 accepted native runs, 671 verified failed attempts, all 97 source segments pass.
- Corrected detector output equals every stored event object; no native recordings were changed.
- All eight modules and 29 student recordings passed all 25 browser groups again after regeneration, without JavaScript errors or failed assets.
- A clean source-only archive passed the existing browser suite using direct file opening.

## Scope rulings

The review did not rerun PSCAD, change compiler, or establish hardware recovery/thermal accuracy, equipment ratings, industrial PLL/current/gamma controls, VDCOL/protection, transformer behavior or full-link performance. These omissions are accepted limits of the original inverter-only educational study, not unresolved defects in its stated scope. The two tested time steps and the tested sag boundary do not establish complete convergence or universal operating limits. Arbitrary malformed inputs and every possible user override were not exhaustively tested. Browser claims apply to the executed Chrome desktop/mobile-viewport tests, not every browser engine or physical device.

The parent release checks own browser execution, PDF appearance, ZIP integrity, current-file and public-history scans, deployment and privacy checks. A successful audit does not replace additional validation needed for equipment design.

## Final release evidence

- The updated 20-page PDF was rendered and visually inspected; equations, figures, tables and pagination remain legible.
- Offline ZIP: 57,807,022 bytes, 132 files. CRC and all packaged dataset bytes verified. Extracted package passed direct-file hub and recovery/comparison checks with no JavaScript errors.
- ZIP SHA-256: `ea158d68394209bb8ada6ba71f7d04b10e3ab0ebcb2bc81f0136767ba506544d`.
- Current shareable checkout scan passed. One old OS-account stamp exists only in excluded development history; no credential-like matches were found in that original history.
- Public history scan passed for commit `fd46852a0eafd3bf5e89d50afc223e97c151e57b`: 622 reachable blobs, no findings. Original development history remains in the local `local-development` branch and `.local/prepublication-history.bundle`; neither was pushed.
- Public repository: https://github.com/angelohafner/hvdc-lcc-commutation-failure-lab . Remote contains only `main` at this verification.
- GitHub Pages: https://angelohafner.github.io/hvdc-lcc-commutation-failure-lab/ . Configured from `main:/docs`; deployment completed successfully at 2026-11-16T22:55:24Z.
- [GitHub validation run](https://github.com/angelohafner/hvdc-lcc-commutation-failure-lab/actions/runs/43974402621) passed dependency installation, 16 Python tests (six native-evidence tests explicitly skipped), current-release audit and all browser groups on a clean Windows runner.
- [Pages deployment run](https://github.com/angelohafner/hvdc-lcc-commutation-failure-lab/actions/runs/43974491508) completed successfully.
- The complete browser suite passed with `LAB_URL` set to the public Pages URL: all eight modules, 29 recordings, desktop/mobile viewport controls and the final local direct-file regression; no JavaScript errors or failed assets. See public_browser_tests.json.
- The published hub was opened and visually verified in the in-app browser. Native simulation results remain the original 31 accepted recordings; this audit did not rerun PSCAD.
- Release assets use the verified offline ZIP and PDF; the release manifest records the ZIP hash above. Subsequent commits recording these audit results change documentation/evidence only.
