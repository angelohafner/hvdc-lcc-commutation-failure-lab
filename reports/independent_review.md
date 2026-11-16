# Independent final review and resolution

The independent read-only reviewer examined the complete model/pipeline/UI, including actual native-derived event windows. It found no Critical issues and four Important issues. No Minor findings were reported.

| Finding | Regression evidence and resolution |
|---|---|
| Nominal 120-degree windows could cross extra same-group gate edges after a reference change; existing incoming current could be mistaken for a new rise | Actual CF-09 gate-window regression and a decaying-incoming-current fixture failed before the fix. Windows now end before the next recorded group edge, and a new transfer requires initially unestablished incoming current and a sustained post-gate rise. Simultaneous group gates remain inconclusive. |
| A current threshold crossing was published as completed overlap before off-state evidence | The near-zero-current fixture failed its null-completion assertion before the fix. Threshold crossing is now a separate field; completion and overlap require reverse-voltage evidence. |
| A refused rerun could still mutate the shareable case project | The pre-existing-evidence test failed before the fix because PSCAD was accessed. The evidence-folder guard now runs before any unload, preparation, load or save. |
| A late current-zero interval could pass an empty slice to convolution and abort processing | A ten-sample late-extinction fixture raised an exception before the fix. Insufficient-length masks now return no sustained condition; incomplete evidence remains inconclusive. |

The tests were observed failing before implementation and passing afterward. All 31 accepted native runs are reprocessed without changing native output. Dependent summaries, event records, browser datasets, scientific figures and reports are regenerated. Final test counts and totals are recorded in the validation report and machine-readable audit.

## Scope decisions after review

The reviewer declined to judge hardware fidelity, equipment ratings, semiconductor recovery accuracy and complete numerical convergence. These remain outside the measured scope; using the model for equipment design would require additional validation.

Industrial controller, PLL, VDCOL and protection performance remain outside the implemented model. The conclusions apply to the explicit fixed/scripted-source experiment rather than an industrial control system.

The prescribed DC reversal/restoration is retained as a disclosed experimental source action. Treating it as a complete rectifier-control design would be unsupported.

At the time of this first review, public deployment was deferred. The owner subsequently resumed publication; see publication_audit.md for the second audit and deployment evidence.

PDF rendering, package integrity and browser compatibility are owned by the release checks. PDF pages are visually inspected and ZIP bytes/CRC are checked. Browser claims are limited to the executed modern Chrome checks, direct-file mode and local static hosting; other engines and future public hosting are not established.
