# Metrics and verification

## What the reference run achieves

The reference run uses a sample Dockerfile and synthetic CI check results. The corrected candidate passes the gate and Purple marks three baseline rules resolved. These results describe the fixture.

| Metric | Baseline | Corrected candidate |
| --- | ---: | ---: |
| Open rules | 3 | 0 |
| Failed required CI checks | 1 | 0 |
| Passing required CI checks | 1 of 2 | 2 of 2 |
| Resolved rules against the baseline | — | 3 |
| Lessons recorded by Purple | — | 3 |
| Regression-check proposals | — | 1 |
| Gate decision | Block | Pass |

The three baseline rules are image pinning, explicit non-root user and dependency policy. The regression proposal comes from the resolved dependency check. The Dockerfile digest is a fixture placeholder, so the run verifies policy behavior without building or deploying an image.

## What to track across CI runs

| Metric | Definition | Data needed |
| --- | --- | --- |
| Registered critical component coverage | Critical components assessed ÷ critical components in the authoritative catalog | Component inventory, CI reports, service catalog |
| Required evidence completeness | Required component-check pairs with a valid result ÷ required pairs | Policy and producer artifacts. Track missing and errored outcomes separately. |
| Gate outcomes | Counts and rates of pass, block and error for completed evaluations | One report per evaluated candidate. Keep error rates visible alongside blocks. |
| Time to verified fix | Median and p90 elapsed time from first blocked result to first valid result marking that component and rule resolved | CI timestamps and check history keyed by component and rule |
| Finding recurrence | Previously resolved component-rule pairs that reopen ÷ pairs eligible for observation in the same window | Historical gate reports, with observation windows and policy versions |
| Lesson adoption | Approved regression requirements ÷ eligible proposals in the period | Review records, learning policy history and Purple lessons |

The report contains gate decisions, findings and evidence hashes. Time-based and historical metrics require retaining and joining reports with CI or Git metadata. Collect a baseline before setting performance targets. A passing report reflects the configured checks, and the metrics above do not require production traces.

Reproduce the example with the [README commands](../README.md#evaluate-ci-check-evidence).

## Counters in the audit report

Completed assessments include component pass, block and error counts and required
check counts for pass, fail, error and missing. Use these counts to compute
per-run evidence completeness and keep execution errors visible. Input validation
errors can occur before these counters are available. The report also includes
the effective component policy hash and a stage trace for each assessed component.
