# BMCManager Architecture

This document outlines the basic architecture of the `bmcmanager` tool.

## `setup.py`

Used for packaging and installing `bmcmanager`. Also, defines all bmcmanager commands as entrypoints under the `bmcmanager.entrypoints` namespace.

## `bmcmanager/config.py`

Handles reading the configuration files.

## `bmcmanager/cliff.py`

Defines the top-level cliff app for `bmcmanager`.

## `bmcmanager/dcim/__init__.py`

Defines available DCIMs. Currently, only NetBox is supported.

## `bmcmanager/dcim/<dcim>.py`

DCIMs are responsible for retrieving information for a specific server.

All DCIMs are defined in their own separate file. DCIMs should sub-class `bmcmanager.dcim.base.DcimBase`, and **must** implement all its methods, along with any other helper methods required by that specific DCIM.

## `bmcmanager/oob/__init__.py`

Defines available OOBs. Currently, Lenovo, Dell and Fujitsu OOBs are supported.

## `bmcmanager/oob/<oob>.py`

OOBs are responsible for implementing operations for a specific server provider.

All OOBs are defined in their own separate file. `bmcmanager.oob.base.OobBase` implements a lot of standard functionality that should work out of the box with any provider. OOBs should sub-class `OobBase`, overriding or extending its methods as needed.

> NOTE: Not all commands are implemented in every OOB.

## `bmcmanager/firmwares/*.py`

Defines `FirmwareFetchers`, which are used by the `bmcmanager firmware latest get` command to check for new firmware versions as well as download firmware bundles.

## `bmcmanager/commands/base.py`

Defines `BMCManagerServerCommand`, `BMCManagerServerGetCommand` and `BMCManagerServerListCommand`. These are the base classes for all `bmcmanager` commands. They handle common command-line arguments, configuration, loading information from the DCIM (e.g. NetBox) and preparing for an OOB operation.

Typically, `bmcmanager` commands need to sub-class one of these and only specify command-specific arguments and the OOB method that should be called.

The three base classes refer to three types of `bmcmanager` commands:

| Base Class                    | Description                                                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `BMCManagerServerCommand`     | Command for a simple operation (e.g. reboot server)                                                                                  |
| `BMCManagerServerGetCommand`  | Command for retrieving information (e.g. IPMI credentials) for a single item. Extends the cliff `ShowOne` command class              |
| `BMCManagerServerListCommand` | Command for retrieving a list of information (e.g. Firmware components and their versions). Extends the cliff `Lister` command class |

## `bmcmanager/commands/**.py`

All commands are implemented here, as explained above.
