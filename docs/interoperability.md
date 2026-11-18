# Interoperability and module boundaries

Keep the gate, swarm plugins, ledger and offline learning in the Python reference
implementation. Integrate other languages at the process boundary so every
consumer gets the same decisions and audit semantics.

| Deployment | Interface | Use |
| --- | --- | --- |
| Python embedding | Standalone Red, Blue and Purple imports or the bundled harness | Trusted Python extensions inside the same application |
| Any CI stack | CLI, exit codes and a versioned JSON report | Release gates in JavaScript, Go, Java, .NET or shell pipelines |
| External evidence producer | Versioned JSON artifact and optional detached signature | Scanner or guardrail jobs written in any language |
| Containerized consumer | Current Compose demo and Python wheel | Offline demonstration or embedding in an existing trusted runner |

The [evidence schema](../cyberops/contracts/ci-evidence.v1.schema.json) defines the
wire format. The consumer validates one result per component and check and
compares the artifact revision with trusted CI metadata. The
[report schema](../cyberops/contracts/gate-report.v1.schema.json) defines the
stable consumer fields. Other report fields are additive. Consumers must reject
unsupported schema versions and interpret exit codes as 0 for pass, 1 for block
and 2 for error. Signature and provenance checks remain separate from schema
validation.

## Node.js consumer

Generate a report using the [evidence example](enterprise-resilience.md#try-the-exposure-queue).
Then run:

```sh
node examples/interop/read-report.mjs /tmp/cyberops-exposure.json \
  1111111111111111111111111111111111111111
```

The example prints a compact result and exits 1 for the blocked fixture.
Supply the expected SHA from trusted CI metadata and the report from an
authenticated artifact channel. The consumer performs envelope and revision
checks. The JSON Schema files are available for integrations that need wider
structural validation.

Add an HTTP or gRPC adapter when multiple remote clients need a shared service.
Keep authentication, authorization and version negotiation at that boundary.
The offline CLI and schemas are the current cross-language interfaces.
