# Extending

This document describes extending `bmcmanager`.

## Adding a new DCIM

- Create a new file under `bmcmanager/dcim`, extend `bmcmanager.dcim.base.DcimBase` and implement all required methods. You can use the NetBox implementation as a reference point.

- Add the new dcim in the `DCIMS` dict at `bmcmanager/dcim/__init__.py`.

- Document example configuration in `README.md`, and add a new file under `docs/` if deemed appropriate.

## Adding a new OOB

- Create a new file under `bmcmanager/oob`, extend `bmcmanager.oob.base.OobBase` and override the methods that you want. You can use any of the existing OOBs as reference.

- Add the new oob in the `OOBS` dict in `bmcmanager/oob/__init__.py`.

## Adding a new bmcmanager command

- Implement the new functionality as an OOB method in `bmcmanager/oob/*.py`. If possible, try to implement in a standard way, so that it fits in `OobBase`. If it is provider specific, do not forget to add an empty implementation in `OobBase` that raises a `NotImplementedError`.

- Create the class for the new command under `bmcmanager/commands/*.py`.

- Add the entry point of the command in `setup.py` (under the `bmcmanager.entrypoints` namespace) and re-install package for it to take effect.

## Adding a new firmware fetcher

- Create a new file under `bmcmanager/firmwares`. Extend the `bmcmanager.firmwares.LatestFirmwareFetcher` class and implement the required methods. Use any of the existing implementations as a reference point.

- Add the firwmare fetcher in the `firmware_fetchers` dict at `bmcmanager/firmwares/__init__.py`.
