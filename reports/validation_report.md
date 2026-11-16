# Local release validation

## Engineering evidence

- 31 accepted native PSCAD executions, with successful build/run receipts, 38 native channels and retained project/output SHA-256 hashes. One initial DC-ground-path model was rejected and excluded.
- Final detector total: 671 verified failed firing attempts across independent recordings. Inconclusive attempts are retained. Two resumed-conduction events have reverse-voltage evidence; current dips without that evidence are inconclusive.
- Baseline: correct firing order, approximately 120 degree gate widths, finite overlap, positive DC-to-AC power, negative bridge voltage, stable late-record cycle means and both valve-group current balances.
- All accepted records pass uniform timing, finite data, duration, native channel integrity, AC source reconstruction, DC source reconstruction, disturbance-window and KCL checks. The audit is `results/summary/engineering_audit.json`.
- The principal sag failure is visually confirmed from outgoing/incoming currents, outgoing valve voltage, gate commands and reversed driving voltage. Selected PNG/SVG oscillograms and full-precision CSV samples are retained.
- CF-13-R2 has successful attempts from 0.50612 s, recovery established at 0.52278 s, and a new verified failure firing at 0.57278 s. REC-NOMINAL is the matched stable-restoration comparison. There is one external AC sag in each.
- 10 versus 5 microsecond checks preserve zero baseline failures and 30 sag failures. Peak-current changes are approximately 0.766% and 0.00233%, respectively. This is bounded sensitivity evidence, not full convergence.

## Detector and pipeline regression checks

`py -3.11 -m unittest discover -s tests -v` checks successful transfer, low margin without failure, retained outgoing current, resumed conduction, missing voltage, false near-zero-current evidence, a new outgoing gate, recovery/recurrence counting, sample timing, SI conversion, project hash rejection and the corrected DC return path. Native evidence tests explicitly skip on a source-only checkout until PSCAD is reproduced.

Regression evidence includes observed failing tests followed by passing fixes for the original grounded DC return, near-zero current without reverse bias, loss of established recovery after an inconclusive attempt, changed project hashes, and the browser's selected-valve legend.

## Browser and educational audit

The Playwright check in `tests/test_html/interaction.cjs` was executed against actual local data. It checks all eight pages at 1440 px and 390 px widths, playback/pause/reset, cursor input, speed, zoom/pan, event focus, signal selection, guide steps, circuit enlargement, selected valve legend, PNG download, study/presentation state, mathematical rendering, case loading, failure filtering, event selection, graphical valve tasks, quiz feedback/scoring/reset, and direct `file://` comparison loading. The machine-readable result is `reports/browser_tests.json`.

Each module provides an objective, relevant prior knowledge, an explanation, a recorded demonstration, takeaways and practice. The circuit is generated with native Schemdraw SCR/source/IEEE-resistor symbols. Source orientation and physical connections were visually corrected; measured-current states are distinct from gates, and all states have textual labels. The shared waveform scales and recorded cursor support normal/failure comparison. Beginners can hide advanced parameter/provenance details; presentation mode pauses playback without losing the selected recording.

The current UI declares measured data, units, native time resolution, individual case parameters, float32 conversion bounds and source hashes. It neither creates unsupported waveforms nor calls a low-gamma event a failure by itself.

## Scope and limits

The checks validate this original inverter-only educational study. They do not establish semiconductor charge-storage fidelity, equipment ratings, protection operation, an industrial VDCOL/current/gamma controller, PLL behavior, transformer zero-sequence behavior, full HVDC-link performance or universal critical sag limits. Large persistent currents reflect the unlimited scripted DC equivalent. Some operating-point changes also change pre-fault current.

Direct file opening and localhost hosting are tested. The owner resumed publication on 16 November 2026. Live deployment evidence is maintained in publication_audit.md. Public release candidates exclude native solver/library binaries, raw bulk outputs, temporary files, credentials and unrelated local data. Full-precision local processed NPZ arrays remain available in this workspace; the repository carries selected CSV windows, metadata, events, summaries and browser recordings.


## Final review resolution

The independent reviewer reported four Important findings and no Critical or Minor findings. Each was reproduced by a failing regression before the correction: actual gate-window bounds and incoming-current rise; suppression of unsupported completion/overlap values; refusal of reruns before model mutation; and safe handling of incomplete late-window evidence. The final Python suite has 19 passing tests. Reprocessing the unchanged 31 native recordings yields 671 verified failed attempts, superseding the interim 799 count. The baseline, first sag failure and recovery-then-recurrence demonstration remain established. See independent_review.md for the findings and scope decisions.


## Publication audit update

The second independent review found two Important robustness gaps and one Minor teaching inconsistency. All were corrected. Contradictory returned-current/voltage evidence remains inconclusive. The source-profile audit now checks 97 separate pre-event, disturbance, DC-suppression and restoration segments, independently for every AC phase and the DC source, with 1 ms excluded at segment boundaries. Each segment must have at least three samples and median residuals below 1,000 V. The largest accepted AC residual is 182.757 V; the largest DC residual is 1.545 V. Removing the CF-02 sag or CF-08 DC step from metadata now fails the audit; both regressions were observed failing before the fix.

The updated detector reproduces all 3,805 stored event objects exactly; no native result or waveform changed. There are 22 passing local Python tests. Six native-evidence tests skip explicitly on a source-only clone. The guide now requires reverse-voltage evidence to confirm the end of measured overlap. See publication_audit.md for packaging, history and live deployment results.
