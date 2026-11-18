# CyberOps 0.2.0

This pilot package adds the browser operator console and its role-based local API.

- [Python wheel](cyberops-0.2.0-py3-none-any.whl)
- [SHA-256 checksum](SHA256SUMS)
- [Installation, browser quickstart, and API](../../docs/operator-console.md)

The installed wheel passed all 21 tests on Python 3.12. A Chromium smoke test
connected, filtered and opened a finding, imported cases, recorded a priority
review, verified the queue update, and disconnected. The console is designed
for a single repository on a loopback interface. A shared enterprise service
still needs managed identity, TLS, centralized audit, and recovery validation.
