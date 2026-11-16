# Original standalone inverter model

The authoritative native files are `../inverter_6_pulse/lcc_inverter.pscx` and the individually executed `../simulation_cases/LCC_*.pscx` projects. The full engineering discussion is in `../../docs/technical_report.html`.

| Native node | Meaning |
|---|---|
| P | Common cathodes of upper valves T1, T3, T5; positive DC-current reference leaves this terminal toward the smoothing reactor |
| N | Common anodes of lower valves T4, T6, T2; positive terminal of the floating DC voltage equivalent |
| A, B, C | Converter phase terminals between upper/lower valves and commutation inductances |
| BUS_A, BUS_B, BUS_C | PCC nodes between commutation inductance and grid resistance/inductance; fault branches connect here |
| DCSRC | Negative terminal of the floating DC equivalent; connected through the series DC resistance/reactor to P |

Electrical node labels make connections explicit without long crossing wires. Signal data labels are separate from electrical node labels. Phase sources are individually grounded. The DC source and differential P-N voltage measurement do not ground N.

Upper valves: T1=A, T3=B, T5=C, phase-to-P current. Lower valves: T4=A, T6=B, T2=C, N-to-phase current. Gates T1 through T6 rise every 60 electrical degrees, each held for 120 degrees. T1's nominal gate occurs at `30 + alpha` degrees of the phase-A source clock.

Native `master:peswitch` components use thyristor mode, integer external gates, 0.01 ohm on resistance, 100 Mohm off resistance, disabled snubber, and 200 microseconds minimum extinction time. `LabController` is an original custom definition, not a copied PSCAD library model. Its Fortran schedules source profiles, the firing clock and fault commands. No complete HVDC control or protection is present.

All base parameters are in `config/model_parameters.json`. The scripts set native electrical R/L values as well as controller profile parameters. Case definitions and execution receipts distinguish inputs from measurements. Optional `scr`, `dc_current_reference_a`, and `gamma_reference_deg` calculate feedforward initial settings; they do not regulate those quantities.

The recovery follow-up has a prescribed DC command after AC clearing. A negative multiplier reverses the ideal equivalent voltage to suppress current. The nominal-restoration and overshoot runs share that suppression. This is an explicit experimental source action, not a verified model of rectifier dynamics, VDCOL, blocking, or DC energy availability.

38 native output channels: six currents `IT1..6`, six anode-cathode voltages `VT1..6`, six gates `G1..6`, six native extinction-time monitors `GammaT1..6`, three converter voltages `VACA/B/C`, three PCC voltages `VPCCA/B/C`, three source currents `IGA/B/C`, DC voltage/current, firing reference, disturbance-window flag, and source sag factor. The event detector independently measures reverse-bias intervals; it does not blindly use the native gamma monitor. Native kA/kV outputs are converted to A/V before processing.

Rebuild the topology only in its owned destination with `python/build_model.py --port PORT`. Original source projects and copied executed projects are independent; changing the generator does not change archived evidence. Reusing a raw case ID is refused.
