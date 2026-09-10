# Security and disclosure correctness

This project processes local HTML and publisher-declared facts. Do not feed untrusted manifests to a privileged publishing process, run unreviewed agent edits, or point the publisher at a source repository containing secrets. Use a dedicated public build directory and keep evidence records outside it.

The tool does not detect every AI asset, authenticate declared origin or certify legal compliance. Treat stale records, missing notices, incorrect exemptions and hidden disclosures as correctness issues even when they are not security vulnerabilities.

For sensitive reports, use the repository's private security advisory reporting when enabled. Do not post secrets, private content, personal data or exploit details in public issues. Include the affected version, minimal reproduction and impact. Public non-sensitive correctness reports can use an issue with anonymised input and expected behaviour.

The maintainer will triage reports and publish fixes with migration guidance. No response-time SLA or external security audit is claimed. Before production use, pin a release, test the integration on your site's actual pages and monitor upstream release notes.
