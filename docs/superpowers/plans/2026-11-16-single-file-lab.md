# Self-contained virtual laboratory

The owner requested one English HTML file that preserves the eight existing modules, report, real PSCAD recordings and all interactions, with no server or external runtime dependencies.

Use a small navigation shell with persistent, lazily created embedded documents. This preserves each existing module's engine and state without rewriting the validated teaching interface. Package CSS, KaTeX/fonts, SVGs, report figures, licenses and all 29 student recordings directly in the file. A shared lazy decoder supplies the original datasets to each module. No waveform is resampled or synthesized. Optional external reference links are not runtime dependencies. Keep the original multipage site unchanged.

1. Add a reproducible `python/build_single_file.py` bundler. Output `dist/HVDC_LCC_Virtual_Laboratory.html` and an integrity manifest. Fail on missing resources or source dataset hash mismatches. Rewrite local navigation into internal routes; embed all report images and font URLs.
2. Preserve module state with persistent frames; pause the outgoing module, support browser Back/Forward and direct hash entry, and use a viewport-sized frame so dialogs remain visible. Include all licensing notices in the artifact. Decode datasets only on demand and share them across modules.
3. Add static/data tests: embedded resource closure, all 29 payloads equal their authoritative browser-source payloads, and every signal sample equals the native-derived float32 value where local NPZ evidence exists. Test the artifact copied alone to a temporary folder.
4. Add browser integration checks with network disabled and HTTP requests treated as failures: all modules and the report, controls/plots/export, state retention and paused navigation, assessment, case comparison, all recordings, formula/font rendering, mobile layout, keyboard/dialog behavior, history and deep links.
5. Independently review the implementation, fix findings, and record exact checks, artifact size and hash in `reports/single_file_validation.md`. Deliver the standalone HTML. No new PSCAD runs are needed because recorded data and model remain unchanged.

Review focus: hidden-frame playback, accidental relative or network resources, duplicated dataset decoding, lost quiz/cursor state, and off-screen dialogs on mobile.
