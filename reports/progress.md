# Execution ledger

Plan: docs/superpowers/plans/2026-11-16-hvdc-lab.md

The user's autonomous execution request authorizes implementation and publication without repeated confirmation. The workspace was empty on inspection.

Ruling: use the requested static GitHub Pages architecture, with locally bundled assets, rather than Sites hosting or a single standalone HTML. This follows the explicit multi-page repository specification.

Ruling: implement directly in this new isolated project directory on main, as requested for initial publication. There is no existing work to isolate in a worktree.

Environment observed: Windows, PSCAD 5.1.0 x64, mhi.pscad 3.1.2 in Python 3.11, Python 3.14 also installed, GFortran 8.1/13.2 and Intel directories present. Git 2.56 available. gh is not on PATH; further discovery pending. NumPy, Matplotlib, PyYAML, and Schemdraw are available.


User steering: continue locally; publish later. Public repository creation, upload, and Pages deployment are deferred. No successful publication is claimed.

Task 1: Native model compiled and executed using the active professional license and GFortran 8.1. A first run was rejected because a grounded DC return bypassed the lower valve group. The source was changed to a floating two-terminal equivalent and the DC voltage to a differential measurement. A current-balance regression failed before this correction and passed afterward. The rejected run is retained only under ignored results/raw/REJECTED_DC_GROUND_PATH.

Task 2: Baseline CF-00 and sag CF-02 executed. Native file hashes, 10 us uniform sample timing, 38-channel integrity and full duration verified. Eight tests passed. Baseline has zero classified failures and about 28.8 degree minimum measured reverse-bias interval. The first CF-02 failure is T3 to T5 at firing time 0.30278 s: outgoing T3 current never reaches zero, incoming T5 current rises then collapses, T3 voltage stays conducting, and the measured PCC commutation voltage reverses near 0.30508 s. Both normal and failed detail plots were visually inspected. CF-02 overcurrent remains after clearing; post-clearing failures alone are not yet evidence of successful recovery followed by subsequent failure.

Tasks 3 and 4: 31 accepted native simulations; final detector counts 799 failed firing attempts. A near-zero current dip without reverse voltage is now inconclusive (regression RED to GREEN). Recovery is established after six consecutive successful attempts and remembered across intervening inconclusive attempts; CF-13-R2 provides one recurrence episode after recovery. Browser source conversion is checked against full-precision CSV windows. All eight pages pass desktop/mobile, controls, exercises, math and direct file-opening checks. Fifteen Python tests pass.

Task 5: Added original model documentation, complete case interpretations, 20-page-class HTML/PDF report, engineering audit, reproduction instructions, license and third-party notices. Shareable native projects redact only creator/revisor OS-account stamps and retain executable equivalence to archived cases; mappings preserve both hashes. Native raw outputs and full float64 NPZ recordings remain local. Public deployment remains deferred by user instruction. Independent final review and local packaging are next.


Final: fixed actual-gate window bounds and new incoming-current evidence - test_actual_gate_bounds_angle_change_attempt and test_existing_incoming_current_that_only_decays_is_not_a_new_transfer RED-to-GREEN, suite 19/19.
Final: fixed unsupported completion/overlap markers - test_near_zero_current_without_blocking_is_not_resumed_conduction RED-to-GREEN, suite 19/19.
Final: fixed mutation before refusing an existing run - test_existing_evidence_refuses_run_before_any_pscad_or_file_mutation RED-to-GREEN, suite 19/19.
Final: fixed empty late-window convolution - test_extinction_at_window_end_remains_inconclusive_without_crashing RED-to-GREEN, suite 19/19.
Final: native outputs are unchanged; the stricter final classification gives 671 verified failed attempts across 31 accepted runs, superseding the interim 799 count.
Final: Ruling: hardware fidelity, equipment ratings and complete convergence remain outside the measured model scope - applying these results to equipment design would require additional validation.
Final: Ruling: industrial controller, PLL, VDCOL and protection performance remain outside the implemented model - conclusions cannot establish industrial controller performance.
Final: Ruling: prescribed DC reversal/restoration remains a disclosed experimental source action - interpreting it as a complete-link controller would be unsupported.
Final: Ruling: public deployment remains deferred per the owner - there is no live public URL to verify in this session.
Final: Ruling: PDF/package review is handled by final render/CRC checks; browser claims remain limited to executed modern Chrome/direct-file/local-server checks - other engines and future hosting need their own verification.

Final release checks: 19 Python tests and 25 browser check groups passed; all 29 student datasets loaded. The extracted offline ZIP passed direct-file browser checks; archive CRC and dataset bytes match. The 20-page PDF was rendered and visually inspected. Keeping local main and the original workspace per the owner; no push or public deployment. No deferred Minor review findings.


Publication resumed by the owner on 16 November 2026. A second independent review found two Important issues (contradictory returned-current evidence and whole-record source residuals hiding short mismatches) plus one Minor guide wording issue. All were corrected with three observed failing-then-passing regressions. The 22-test suite and all 97 source segments pass. Corrected classification reproduces every stored event exactly. Publication starts from an audited snapshot; original local history is retained because an early project revision contains an OS-account author stamp. The detailed publication record is reports/publication_audit.md.
