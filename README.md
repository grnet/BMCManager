BMCManager
==========

`bmcmanager` is a tool for performing operations on rack units.

`bmcmanager` is released under the terms of the GPL-3.0 license

This is a fork of the `rackops` tool, with bug-fixes, improvements and lots of additional functionality. The original `rackops` tool can be found [here][1].

It currently supports Netbox hosts and the Lenovo, Fujitsu, Dell providers.

To add a host or provider read [CONTRIBUTING.md](docs/CONTRIBUTING.md).

Installation (using Pip)
========================

1.  Install `ipmitool`, `ipmi-sensor`, `ipmi-sel` and `ipmi-dcmi`.

    For Ubuntu/Debian: `sudo apt-get install freeipmi ipmitool`.

    For CentOS/Fedora: `sudo yum install freeipmi ipmitool`.

1.  (Optional) Install `osput` for Lenovo firmware upgrades.

    For CentOS/Fedora:

    ```
    wget https://download.lenovo.com/pccbbs/thinkservers/osput_1.3.2.zip
    unzip osput_1.3.2.zip
    yum install -y OSPUT-1.3.2/osput-1.3.2-1-rhel.x86_64.rpm
    ```

1.  `git clone https://github.com/grnet/bmcmanager`

1.  `cd bmcmanager && pip3 install .`

If you get errors for missing binaries, but you want to install anyway, do `env BMCMANAGER_IGNORE_MISSING_BINARIES=1 pip3 install .` instead.

Installation (Snap)
===================

`bmcmanager` is also available as a snap package.

1.  `sudo snap install bmcmanager`.

The Snap package is installed with `strict` confinement, so it is not allowed to read your files. If you want to use a config file, you need to put it under the `SNAP_COMMON` directory, which typically is `/var/snap/bmcmanager/common`.

Configuration
=============

`bmcmanager` uses a single configuration file. It defaults to `~/.config/bmcmanager` or `$XDG_CONFIG_HOME/bmcmanager` if the environment variable `$XDG_CONFIG_HOME` is set, but a different configuration file can be used using the `-c` command line argument.

The configuration file should have this form:

```ini
[<DCIM1>]
api_url = <api_url1>
netbox_token = <netbox_api_token>           ; optional, NetBox API token

[<DCIM2>]
api_url = <api_url2>

[<OOB1>]
username = <oob1_username>
password = <oob1_password>
nfs_share = "IP:/path/"
http_share = "http://IP/path/"
credentials = <dcim_secret_name_for_credentials>

; Latest firmware versions to check against
bios = <MAJOR.MINOR.PATCH>
tsm = <MAJOR.MINOR.PATCH>
psu_<model> = <MAJOR.MINOR.PATCH>
expected_psus = 2

[<OOB2>]
username = <oob2_username>
password = <oob2_password>
nfs_share = "IP:/path/"
http_share = "http://IP/path/"
```

where:
- `<DCIM>` is the name of a dcim. Currently we only support the `netbox` dcim.
- `<api_url>` is the API URL of the specified DCIM.
  (i.e https://netbox.noc.grnet.gr/)
- `<OOB>` is the name of an oob (i.e. lenovo)
- `<username>` is the username associated with a specific oob.
  while
- `<password>` is the password that will be used for a specific oob.
- `nfs_share` is the nfs share where diagnostics from Dell hosts are uploaded,
- `http_share` is an http share where Dell hosts retrieve idrac updates from,

If environment variables for the above values are defined, they will overwrite
those from the configuration file. The environment variables supported are:

- `BMCMANAGER_USERNAME`
- `BMCMANAGER_PASSWORD`
- `BMCMANAGER_NFS_SHARE`
- `BMCMANAGER_HTTP_SHARE`

If command line arguments for the username and password are defined, they will overwrite those from the configuration file and the environment variables.

Usage
=====

`bmcmanager` can work as a CLI module or a python3 module.

CLI
===

`bmcmanager <command> <identifier>`

The non-required command line arguments are:

- `-d`, `--dcim`. Name of the DCIM to be used. Defaults to `netbox`.
- `-r`, `--rack`. The identifier provided is an identifier for a rack.
- `-a`, `--rack-unit`. The identifier provided is an identifier for a rack unit.
- `-s`, `--serial`. The identifier provided is an identifier for a serial.
- `-c`, `--config`. The location of the configuration file.
- `-u`, `--username`
- `-p`, `--password`. With this argument if the password is not provided as a string, the user will be prompted for entering a password.
- `-f`, `--force`. Some commands can be run with this argument. See `Commands` for more details.
- `-w`, `--wait`. Some commands can be run with this argument. See `Commands` for more details.
- `-v`, `--verbose`. Set log level to INFO, and DEBUG for `-vv`.


As a module
===========

1. `from bmcmanager.bmcmanager import BMCManager`

2. `bmcmanager = BMCManager(command, identifier, is_rack, is_rack_unit, is_serial, command_args, args, config, environment_variables)`.
    - `config` should be a hash table with the values defined in the *Configuration* section.
    - `args` should be a hash map containing the command line arguments specified above as keys (i.e. {"wait": True})
    - `is_rack`, `is_rack_unit`, `is_serial` are boolean values specifying if the identifier corresponds to a rack, rack unit or serial respectively.
    - `command_args` is a list containing arguments for the command to be run.
    - `environment_variables` is a hash map containing the environment variables
   specified above.

3. `bmcmanager.run()`

Commands
========

Run `bmcmanager --help` to get a list of all available commands. Some typical
commands are:

- `info`: Print information regarding the machine.
- `console`: Opens a Java console on the remote machine.
- `open`: Opens the IPMI host url on the client machine.
- `status`: Prints information regarding the status of the remote machine.
- `power-status`: Prints whether the machine is on/off.
- `power-on`: Powers on the machine.
- `power-off`: Sends a signal to the operating system for shutoff. Can be run with the `--force` command line argument for a hard shutoff. Can be run with the `--wait` argument to wait until the operating system shutoff is complete before exiting.
- `power-cycle`: Soft restart.
- `power-reset`: Hard restart.
- `boot-pxe`: Force pxe boot.
- `boot-local`: Force boot from default harddrive.
- `ipmi-reset`: Restart ipmi device. Can be run with the `--force` command line argument for resetting the ipmi device.
- `ipmi-logs`: Print system event logs.
- `clear-ipmi-logs`: Clear system event logs.
- `ipmi-ssh`: Open interactive SSH session with IPMI.
- `system-ram`: Print available system RAM.
- `diagnostics` : Initiate diagnostics report on Dell ipmi and export it to an nfs share
- `autoupdate`: Schedule auto updates on a Dell host every day at 08:30
- `upgrade`: Instantly update an iDrac's firmware from an http share
- `idrac-info`: Receive BIOS version and controller info from an iDrac

[1]: https://github.com/grnet/rackops.git "Rackops GitHub repository"
