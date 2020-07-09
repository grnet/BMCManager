# BMCManager

## Introduction

[`bmcmanager`](https://github.com/grnet/bmcmanager.git) is a tool for performing operations on rack units. It originated as a [`rackops`](https://github.com/grnet/rackops.git) fork, but has since been re-written almost from scratch, offering lots of additional functionality, bug-fixes and all-around improvements.

`bmcmanager` supports Lenovo, Dell and Fujitsu servers, and relies on [`NetBox`](https://netbox.readthedocs.io/en/stable/) for DCIM and IPAM.

`bmcmanager` is released under the terms of the GPL-3.0 license.

## Features

`bmcmanager` features include and our not limited to:

- Manage SEL and IPMI sensor readings.
- Get information for system RAM, disks, power status.
- IPMI management commands (power on, power off, power cycle, reset and more).
- Check for latest firmware versions and perform firmware upgrades.
- Nagios/Icinga compatible IPMI server checks (sensors, logs, disks, and more).
- Open console (requires JavaWS).
- Manage NetBox secrets.
- Configure unique IPMI credentials per server, store them as NetBox secrets and retrieve them automatically from NetBox.
- Bash auto-completion.
- Supports multiple output formats supported.

## Installation

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
   $ git clone https://github.com/grnet/bmcmanager.git
   $ cd bmcmanager
   $ pip3 install .
   $ bmcmanager --help
   ```

### Snap

1. You can install `bmcmanager` as a snap package:
   ```bash
   $ sudo snap install bmcmanager
   ```

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

`bmcmanager` uses a single configuration file. It looks in `~/.config/bmcmanager` and `$XDG_CONFIG_HOME/bmcmanager` by default, but a different configuration file can be chosen by setting the `--config-file` command line argument.

The configuration file should have this form:

```ini
;; Configuration of "netbox" DCIM
[netbox]
; Required
api_url = <netbox_api_url>
; [Optional] Limit bmcmanager to query for certain device types only.
device_type_ids = <id1>, <id2>, ...
; Only if using NetBox secrets for IPMI credentials
netbox_token = <netbox_api_token>
session_key = <netbox_session_key>
; [Optional] Timeout when connecting to NetBox (in seconds).
timeout = 10

;; Configuration of "lenovo" OOB
[lenovo]
; IPMI credentials
username = <username>
password = <password>

; Use secret with role <secret_role> as IPMI credentials. Secret name will
; be used as username, secret plaintext will be used as password. You need to
; set `netbox_token` and `session_key` above for this to work.
; If no secret is available, then `username` and `password` defined above will
; be used instead.
credentials = <secret_role>

; [optional] Configure NFS share and HTTP share (used by some commands)
nfs_share = "IP:/path/"
http_share = "http://IP/path/"

; [optional] Latest firmware versions to check against
; Used by the `bmcmanager firmware check` command
bios = <MAJOR.MINOR.PATCH>
tsm = <MAJOR.MINOR.PATCH>
psu_<model> = <MAJOR.MINOR.PATCH>

; [optional] Number of PSUs to expect per server
; Used by the `bmcmanager firmware check` command
expected_psus = 2
```

Some configuration can be overriden using environment variables:

- `BMCMANAGER_USERNAME`
- `BMCMANAGER_PASSWORD`
- `BMCMANAGER_NFS_SHARE`
- `BMCMANAGER_HTTP_SHARE`

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

The `bmcmanager complete` generates a bash auto-completion script. You can use it directly:
```bash
$ . <(bmcmanager complete)
$ bmcmanager        # pressing tab should show available commands
```

Or add the auto-completion script under `/etc/bash_completion.d/bmcmanager`, so that it is loaded automatically by `bash`:
```bash
$ echo ". <($(which bmcmanager) complete)" | sudo tee /etc/bash_completion.d/bmcmanager
```
