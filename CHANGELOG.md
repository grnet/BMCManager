# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added

### Changed

- Switched to `pbr` for installation.
- Build snap for `amd64` and `arm64` architectures.

### Fixed

- Crashes when the IPMI address was not prefixed with `http://` or `https://`.
- `bmcmanager check sensor` command returned OK status when the underlying commands timed out.

## [v1.0.3] (2020-10-28)

### Added

- `bmcmanager server list` now also prints the server IPMI addresses.

### Changed

### Fixed

## [v1.0.2] (2020-10-02)

### Added

- `bmcmanager firmware latest check --after YYYY-MM-DD` command, to check whether new firmware versions have been released after a specific date.

### Changed

### Fixed

- When a command failed, sometimes a successful return code (0) was returned, along with a false "No servers found" message.

## [v1.0.1] (2020-09-07)

### Fixed

- Compare versions as tuples instead of strings if possible when checking for firmware upgrades.

## [v1.0] (2020-07-09)

### Added

- Bash auto completion.
- Get and list commands now support multiple output formats.
- Interactive mode.
- An error is printed when no servers are matched.
- Command for opening NetBox page (`bmcmanager open dcim`).
- Command for calling ipmitool directly (`bmcmanager ipmi tool`).
- Print possible commands when an invalid command is used.
- Documentation examples.
- Documentation for extending `bmcmanager` with new features.
- Reduced Docker image size.
- `bmcmanager server list` command, to list available servers.
- `timeout` option for NetBox DCIM.

### Changed

- Using [cliff](https://docs.openstack.org/cliff/latest/index.html).
- All commands are now grouped under namespaces, see `bmcmanager --help`.
- Numerous speed improvements by avoiding useless queries to the DCIM.
- Updated documentation, added complete configuration example.
- Config file is now set using the `--config-file` flag.

### Fixed

- Improved log message levels so that no sensitive data is printed unless debugging.
- Command-line arguments handling.
- Show a helpful error message when no DCIM has been configured.
- Try to recover from expired session errors.
- Homogenous argument and command help messages.

## [v0.2] (2020-07-05)

Initial version as `bmcmanager`.

### Added

- Added flake8 tests with tox.
- Documentation for Lenovo hosts.
- `bmcmanager get-firmware` command for Lenovo hosts.
- `bmcmanager refresh-firmware` command for Lenovo hosts.
- `bmcmanager console --print-cmd` argument.
- `bmcmanager check-firmware-latest` command for Lenovo RD350/RD550 Lenovo servers. It can be extended in the future for more servers if needed.
- `bmcmanager creds --ipmi-field (hostname|username|password)` argument.
- `bmcmanager firmware-upgrade` command for Lenovo hosts. Can perform the upgrade using `osput` (`--mode osput`) or RPC calls (`--mode rpc`). Optionally clears log messages afterwards (`--clear-logs` flag).
- `bmcmanager lenovo-rpc` command.
- `bmcmanager clear-upgrade-firmware-logs` command.
- `bmcmanager get-ipmi-address` and `bmcmanager refresh-ipmi-address` commands.

### Changed

- Enforce a single coding style across the code.

### Fixed

- Installation dependencies and instructions.
- Linter warnings.

## [v0.1] (2020-04-13)

### Added

- `bmcmanager clear-ipmi-logs` command, clear system event log.
- `bmcmanager ipmi-ssh` command, open interactive SSH session with IPMI.
- `bmcmanager system-ram` command, check system RAM for Lenovo servers.
- Add BIOS versions in `bmcmanager info` command.
- `bmcmanager (un)lock-power-switch` commands.
- Allow reading system-wide config (from `/etc/bmcmanager` or `/etc/.bmcmanager`)
- Allow using NetBox secrets for username and password.
- `bmcmanager creds` command, show IPMI credentials.
- `bmcmanager ipmi-sensors` command, show IPMI sensors status.
- `bmcmanager check-ipmi` command.
- `bmcmanager check-ram` command for Lenovo servers.
- bmcmanager now says which config files it uses.
- Include NetBox device ID in `bmcmanager info` command.
- `bmcmanager check-firmware` command.
- `bmcmanager get-disks` command for Lenovo servers.
- `bmcmanager ipmi-logs-analysed` command for Lenovo servers.
- `bmcmanager check-disks` command for Lenovo servers.
- Main argument parser uses the unrecognised flags as command arguments. This allows commands to use their own parsers.
- `bmcmanager get-secrets` and `bmcmanager set-secret` commands.
- `bmcmanager set-ipmi-password` command, with ability to store the new password.
- Limit NetBox search results using device type ids.
- `bmcmanager -h` shows available commands.

### Changed

- Updated installation instructions.

### Fixed

- `bmcmanager open` command now works on Linux machines.
- Netbox Token header.
- NetBox DCIM timeout.
- Avoid crashes when NetBox has no IPMI address.
- Fix stale `providers` and `hosts` references in docs.

## [v0.0.1] (2020-03-30)

Initial version.
