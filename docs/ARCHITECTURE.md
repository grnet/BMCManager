`__main__.py`
============

Serves as the entry point. Its responsibility is to retrieve the correct configuration via configuration files, command line arguments and environment variables. It should prompt the user for input when needed. All input passes through this module and all errors regarding user input are generated through this module.

`bmcmanager.py`
============

Serves as the controller of the whole application. Its responsibility is to identify the proper host and provider and call the appropriate methods according to the input it received from its caller.

`dcim`
=======

This directory contains host specific implementations regarding the retrieval of information. All hosts are implemented based on the `DcimBase` interface which defines which methods **must** be implemented and general purpose methods that are generic for each host.

`dcim/<dcim>.py`
=================

The implementation of a specific host. All host specific implementation is contained here.

`oob`
===========

This directory contains provider specific implementations regarding operations on a specific provider (e.g. Lenovo, Dell). All providers are implemented based on the `OobBase` interface which defines which methods **must** be implemented and general purpose methods that are generic for each provider.

`oob/<oob>.py`
=========================

The implementation of a specific provider. All provider specific implementation is contained here.
