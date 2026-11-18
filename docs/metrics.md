# CyberOps metrics

Measure the pre-release path from a change entering CI to a fix being verified. Use the same definitions across pilot repositories and keep results scoped to configured controls.

## The five metrics

| Metric | How to calculate it | What it tells you |
| --- | --- | --- |
| **1. Mean time to detect (MTTD)** | Mean elapsed time from the first eligible CI trigger for a revision carrying a finding to publication of its first valid failed-control result. | How quickly the pipeline surfaces a known control failure. Include CI queue and producer time. |
| **2. Mean time to verified remediation (MTTR)** | Mean elapsed time from the first valid failed-control result to the first valid result verifying that the same finding is resolved on the corrected revision. | How quickly an owner can act and prove the fix. Report unresolved findings and their age alongside MTTR. |
| **3. Critical-component coverage** | Critical components with a completed assessment in the reporting window ÷ critical components in the approved inventory. | How much of the intended scope the gate actually assesses. |
| **4. Required-evidence completeness** | Required component–check pairs with a valid pass or fail result ÷ all required pairs for assessed candidates. | Whether the gate has enough evidence to decide. Report missing and errored results separately. |
| **5. Finding recurrence rate** | Previously verified component–rule pairs that reopen ÷ verified pairs assessed again under comparable policy within the same follow-up window. | Whether fixes and regression controls hold up on later revisions. Count each eligible pair once per window. |

For MTTD and MTTR, show the mean, median, p90, sample size, and measurement window. Use CI timestamps and retain the repository, candidate revision, component, rule, effective policy fingerprint, and report outcome. Count one detection and one verified resolution per finding episode. Treat a missing result or gate error as an evidence problem, and count a resolution only when valid evidence verifies the corrected candidate. When the first eligible trigger is unknown, report detection time as unavailable for that case.

## What is measured today

| Local synthetic measurement | Samples | Median | p90 |
| --- | ---: | ---: | ---: |
| Gate produces a blocked report | 20 | 55 ms | 65 ms |
| Gate evaluates the corrected fixture against its baseline and passes | 20 | 78 ms | 82 ms |

These wall-clock measurements include Python process startup and report writing. The fixture uses the repository's two Dockerfile examples. The run does not include hosted CI queue time, external scanner jobs, or a human making a fix. **Enterprise MTTD and MTTR have yet to be measured.** A CI pilot on a real service is the first opportunity to measure both end to end.

The separate [CI evidence demo](../README.md#evaluate-ci-check-evidence) moves from three open rules to zero and from one of two required checks passing to both passing. Purple records three resolved rules and one regression proposal. The demo verifies gate behavior with synthetic results.

## Report fields and collection

The audit report includes component pass, block, and error counts plus required-check counts for pass, fail, error, and missing. Early input errors may occur before those counters are available. The report also records the effective policy fingerprint and per-component decision stages. Join retained reports with trusted CI timestamps to calculate detection and remediation time. Use the approved service inventory for the coverage denominator.
