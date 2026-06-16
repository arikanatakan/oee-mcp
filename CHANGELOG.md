# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[semantic versioning](https://semver.org/).

## [0.1.0] - 2026-06-16

First release.

### Added

- Analysis tools: `compute_oee`, `oee_from_log`, `oee_from_factors`,
  `aggregate_oee` and `describe_inputs`, returning the oee library's payload
  (factors, time waterfall, six big losses, TEEP, provenance) plus a
  plain-language summary.
- Chart tools: `waterfall_chart`, `loss_pareto_chart` and `trend_chart`,
  returning PNG images.
- stdio server built on FastMCP, with read-only tool annotations.
