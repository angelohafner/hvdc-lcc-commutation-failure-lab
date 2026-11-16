# Self-contained virtual laboratory validation

Delivered artifact: `dist/HVDC_LCC_Virtual_Laboratory.html`.

- Size: 77,154,701 bytes (77.15 MB / 73.58 MiB).
- SHA-256: `eba9d0c4b72ec49cd6c5db6848a1b7f38a6356986f0bd02150c204ed85866b28`.
- Eight interactive modules, complete technical report, report figures, original circuit SVG, styles, JavaScript, KaTeX, all 60 bundled font files, license notices and 29 student recordings are embedded.
- The adjacent manifest is optional audit metadata. Only the HTML is needed at runtime.

## Data fidelity

All 29 source dataset SHA-256 hashes were verified before packaging. Every embedded payload equals its authoritative browser-source payload, including events, units, parameters, quantization bounds and native provenance.

Every embedded signal value was compared with the local native-derived float64 NPZ arrays after the same declared float32 conversion used by the existing laboratory: **1,270,029 sample times and 43,180,986 signal values**. All comparisons passed. The browser decoder's signal-buffer hashes were independently compared with the original encoded source for all 29 recordings. Selected circuit ON/OFF states also matched the full-precision native CSV samples.

No signal is resampled, synthesized or replaced. The student dataset selection is the same as the existing site; the two numerical sensitivity runs remain documented in the report rather than selectable as student recordings. No PSCAD simulation was rerun for this packaging task.

## Browser execution

The file was copied alone into a temporary directory, opened through `file://` in installed Chrome, and tested with browser networking disabled. HTTP/HTTPS or companion-file requests would fail the test. The final run completed **28 check groups**, with zero blocked resource requests, JavaScript errors or CSP errors. Machine-readable evidence is `single_file_browser_tests.json`, bound to the artifact hash above.

Checks cover all modules, all recordings, desktop (1440 x 1000) and mobile viewport (390 x 844), playback, time cursor, zoom/pan, signal selection, valve state, comparison, enlarged diagrams, keyboard dismissal, module links, Back/Forward, direct module hashes, mathematical fonts, scored exercises, graphical valve tasks, reset, PNG export, license display and state retention. Leaving a module pauses its playback. Persistent embedded documents retain cursor, view, valve, learning level and quiz answers during the open session.

Desktop/mobile screenshots were visually inspected for readability and overflow. The report's eight embedded images loaded and all five mathematical expressions rendered. Printing the active report produces **19 nonempty A4 pages** with default browser print margins; text extraction confirmed the final references/licensing section and final sentence. The print regression also confirms normal UI visibility afterward.

## Independent review and applied fixes

The independent read-only review found no critical data-integrity issue and two Important packaging regressions. Both were reproduced by failing browser regressions, corrected and verified in the complete final suite:

1. Intercepting the skip link scrolled to the main content but left keyboard focus in the header. Internal anchors now move focus to their target using a temporary negative tabindex where needed. Enter followed by Tab reaches the recording selector.
2. The viewport-sized frame clipped report printing to one page. During printing, the active rendered document is copied into the top-level print flow, including styles, embedded fonts, images and canvas snapshots. After printing, the temporary print document is removed and the original interactive state is retained.

The reviewer declined new semiconductor/numerical validation because the upstream data and model are unchanged; that boundary is accepted. Parent checks cover the requested visual/interface behavior. Other browser engines, physical mobile devices and optional Internet references were not tested and are not claimed. The documented target remains recent Chrome or Edge; execution was verified in Chrome.

## Static triage and reproducibility

The educational HTML skill's generic scanner requested review for two patterns: `toDataURL('image/png')` was mistaken for a CSS URL, and KaTeX's internal parser method `.fetch()` was mistaken for network fetch. These are false positives: the former exports a local canvas and the latter consumes formula tokens. Embedded resource inspection and the network-disabled browser run found no runtime dependency. Content Security Policy also sets `connect-src 'none'`.

Rebuild with `py -3.11 python/build_single_file.py`. Run `py -3.11 -m unittest discover -s tests -v` and `node tests/test_html/single_file.cjs`. The full final Python suite passes **25 tests** locally. Seven native-evidence tests skip on source-only checkouts; generated artifacts are built before standalone checks in the updated CI configuration. The same standalone build and browser checks are included in GitHub Actions; native arrays remain local and are not prerequisites for the source-only CI checks.

The original multipage site and native evidence remain unchanged. Initial delivery was local; the owner subsequently requested GitHub synchronization. The standalone artifact is distributed with release `v1.1.0`, retaining the verified size and hash above. Closing or reloading the file resets its session state. The file is intentionally large to preserve all student samples and embedded resources.

Publication verification also replaced a fixed 150 ms playback delay in the browser test with a bounded wait for an actual recorded-time change. The original timing assumption failed under concurrent CPU load; the corrected check still requires observed playback and does not change the delivered HTML.
