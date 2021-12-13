# BMCManager

## Introduction

[`bmcmanager`](https://github.com/grnet/bmcmanager.git) is a tool for performing operations on rack units. It originated as a [`rackops`](https://github.com/grnet/rackops.git) fork, but has since been re-written almost from scratch, offering lots of additional functionality, bug-fixes and all-around improvements.

`bmcmananger` supports [NetBox](https://netbox.readthedocs.io/en/stable) and [MaaS](https://maas.io) for DCIM and IPAM.

`bmcmanager` supports Lenovo, Dell and Fujitsu servers out of the box. It also works with any hardware that supports the IPMI 2.0 protocol.

`bmcmanager` is released under the terms of the GPL-3.0 license.

## Features

`bmcmanager` features include and are not limited to:

- Manage SEL and IPMI sensor readings.
- Get information for system RAM, disks, power status.
- IPMI management commands (power on, power off, power cycle, reset and more).
- Check for latest firmware versions and perform firmware upgrades.
- Nagios/Icinga compatible IPMI server checks (sensors, logs, disks, and more).
- Open console (requires JavaWS).
- Manage NetBox secrets.
- Configure unique IPMI credentials per server, store them as NetBox secrets and retrieve them automatically from NetBox.
- Bash auto-completion.
- Command output in multiple output formats (table, json, csv, value).
- (Expiremental) MaaS support. Match servers by hostname, and use MaaS IPMI credentials for all bmcmanager commands.

## Installation

See [GitHub](https://github.com/grnet/bmcmanager/releases)

### Pip

1. Install dependencies:
   ```bash
   # For Ubuntu/Debian
   $ sudo apt-get install freeipmi ipmitool icedtea-netx
   # For CentOS/Fedora
   $ sudo yum install freeipmi ipmitool icedtea-web
   ```

2. (Optional) Install `osput` for Lenovo firmware upgrades.
   ```bash
   # For CentOS/Fedora:
   $ wget https://download.lenovo.com/pccbbs/thinkservers/osput_1.3.2.zip
   $ unzip osput_1.3.2.zip
   $ yum install -y OSPUT-1.3.2/osput-1.3.2-1-rhel.x86_64.rpm
   ```

3. Install `bmcmanager`:
   ```bash
   $ pip install bmcmanager
   $ bmcmanager --help
   ```

### Snap

1. You can install `bmcmanager` as a snap package:
   ```bash
   $ sudo snap install bmcmanager
   ```

Notes:

- The `stable` channel contains the latest stable release.
- The `edge` channel always contains the latest successful `bmcmanager` build from the `master` branch.
- The `candidate` channel contains the latest release candidate version.

Snap Limitations:

- The snap package is installed with `strict` confinement, so it is not allowed to read your files. If you want to use a config file, you need to put it under the `SNAP_COMMON` directory, which typically is `/var/snap/bmcmanager/common`.
- The snap package does not contain JavaWS, so opening a console is not possible.

### Docker Image

1. Development and Release Docker images for `bmcmanager` are available at [DockerHub](https://hub.docker.com/r/cloudeng/bmcmanager):
   ```bash
   $ docker pull cloudeng/bmcmanager
   $ docker run --rm -it --entrypoint bash cloudeng/bmcmanager
   > bmcmanager --help
   ```

Docker Limitations:

- The docker image does not contain JavaWS, so opening a console is not possible.

## Configuration

`bmcmanager` uses a single configuration file. By default, it looks for configuration in the following files:

- `~/.config/bmcmanager.conf`
- `~/.bmcmanager/bmcmanager.conf`
- `bmcmanager.conf`
- `/etc/bmcmanager.conf`
- `/etc/bmcmananger/bmcmanager.conf`
- `~/snap/bmcmanager/common/bmcmanager.conf` (for snap installs)

The configuration file should have this form. Also refer to the [sample config file](./bmcmanager.sample.conf):

```ini
[DEFAULT]
; Define three DCIMs, "netbox", "maas" and "local"
available_dcims = netbox, maas, local

; Use the "netbox" DCIM by default.
default_dcim = netbox

; Map unknown manufacturers to an OOB class implementation for the bmcmanager commands.
; For example, for servers where the manufacturer is `supermicro` or `hp`, use the `base`
; OOB class
oob_overrides = supermicro:base, hp:base

; Configuration of the "local" DCIM.
[local]
type = local

; Configuration of the "netbox" DCIM.
[netbox]
type = netbox
netbox_url = https://netbox.example.com/
netbox_api_token = <netbox_api_token>

; If using NetBox secrets for IPMI credentials.
; Make sure to configure a secret with role `ipmi-credentials` for each server.
; The secret name is the IPMI username, and plaintext is the IPMI password.
netbox_session_key = <netbox_session_key>
netbox_credentials_secret = ipmi-credentials

; Configuration section of the "maas" DCIM.
[maas]
type = maas
maas_api_url = https://maas.internal.deployment:5240/MAAS/api/2.0
maas_api_key = <maas_api_key>
maas_ui_url = https://maasa.internal.deployment:5240/

; Configuration of "lenovo" OOB. This applies to servers with manufacturer "lenovo".
; Add similar sections for each manufacturer (e.g. `dell`, `hp`, ...)
[lenovo]
; Default IPMI credentials. These will only be used if bmcmanager cannot retrieve
; them from the DCIM.
username = <username>
password = <password>

; [optional] Configure NFS share and HTTP share (used by some commands)
nfs_share = "IP:/path/"
http_share = "http://IP/path/"

; [optional] Number of PSUs to expect per server
; Used by the `bmcmanager firmware check` command
expected_psus = 2

; Mapping of expected firmware versions for each server component.
; Used by the `bmcmanger firmware check` command
expected_firmware_versions = bios:3.4.0, tsm:5.14.23
```

To use:

```bash
$ bmcmanager power status lar0510
$ bmcmanager power status lar0510 --dcim maas
```

## Examples

- Retrieve the system event log for server `lar0510`:
  ```bash
  $ bmcmanager ipmi logs get lar0510
  $ bmcmanager ipmi logs get lar0510 --analysed    # Decode OEM fields
  ```

- Clear the system event log for server `lar0510`:
  ```bash
  $ bmcmanager ipmi logs clear lar0510
  ```

- Nagios check for IPMI sensor readings:
  ```bash
  $ bmcmanager ipmi sensor check lar0510
  ```

- Get information for disks attached to server:
  ```bash
  $ bmcmanager disks get lar0510
  ```

- Get latest firmware versions for `thinkserver-rd550` servers, and download firmware bundles in `/opt/firmware-bundles`:
  ```bash
  $ bmcmanager firmware latest thinkserver-rd550 --download-to /opt/firmware-bundles
  ```

- Get firmware version for a server:
  ```bash
  $ bmcmanager firmware get lar0510
  $ bmcmanager firmware get lar0510 -f json
  ```

- Perform a BIOS firmware upgrade using the `bios-v495.bdl` file:
  ```bash
  $ bmcmanager firmware upgrade rpc lar0510 --bundle bios-v495.bdl
  ```

- Open JavaWS console:
  ```bash
  $ bmcmanager open console lar0510
  ```

- Power cycle server:
  ```bash
  $ bmcmanager power cycle lar0510
  ```

- Connect to BMC using SSH:
  ```bash
  $ bmcmanager ipmi ssh lar0510
  ```

- Change IPMI password and store in a NetBox secret with role `MY_SECRET_ROLE`. In the config file, set `credentials = MY_SECRET_ROLE` so that `bmcmanager` will use that automatically:
  ```bash
  $ export BMCMANAGER_USERNAME="DEFAULT_USER"
  $ export BMCMANAGER_PASSWORD="DEFAULT_PASS"
  $ bmcmanager ipmi credentials set lar0510 --new-password "NEW_PASSWORD" --secret-role "MY_SECRET_ROLE"
  $ bmcmanager ipmi credentials get lar0510
  ```

- Activate SOL for a MaaS host:
  ```bash
  $ bmcmanager ipmi tool --dcim maas HOSTNAME sol activate
  ```

## Usage

Use `bmcmanager --help` for a list of available commands. Common command-line arguments for all supported commands are:

| Parameter            | Type   | Description                                                                             |
| -------------------- | ------ | --------------------------------------------------------------------------------------- |
| `--config-file FILE` | String | Read configuration from `FILE`                                                          |
| `--log-file FILE`    | String | Write detailed logs to `FILE`                                                           |
| `--verbose`          | Flag   | Print verbose details. **NOTE**: This may include sensitive information, like passwords |

Most `bmcmanager` commands have the following format:
```bash
$ bmcmanager <command-name> <server-name>
```

`bmcmanager` searches NetBox using `<server-name>` as query string and executes the command for all matching devices.

The server selection arguments are:

| Parameter        | Type                               | Default  | Description                                                                            |
| ---------------- | ---------------------------------- | -------- | -------------------------------------------------------------------------------------- |
| `<server-name>`  | String                             | -        | Search NetBox for `<server-name>` and execute command on all matching devices          |
| `-d/--dcim DCIM` | String                             | `netbox` | Use a different `DCIM`. Requires a separate `[DCIM]` section on the configuration file |
| `-t/--type TYPE` | `name`/`rack`/`rack-unit`/`serial` | `name`   | Specifically match a rack, a rack unit, a serial number, or search by name             |

Also use the `--help` flag to get more information for a particular command, e.g.:

```bash
$ bmcmanager ipmi logs get --help
```

## Auto-completion

>NOTE: Auto-completion is enabled by default when using the snap package.

The `bmcmanager complete` generates a bash auto-completion script. You can use it directly:
```bash
$ . <(bmcmanager complete)
$ bmcmanager        # pressing tab should show available commands
```

Or add the auto-completion script under `/etc/bash_completion.d/bmcmanager`, so that it is loaded automatically by `bash`:
```bash
$ echo ". <($(which bmcmanager) complete)" | sudo tee /etc/bash_completion.d/bmcmanager
```
