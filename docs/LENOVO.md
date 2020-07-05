# Lenovo

Lenovo Thinkservers expose an ASP.NET REST API for performing most of their management tasks over a CLI.

Apart from the generic management commands that use the IPMI interface, we use this REST API to speed up the management process. Lenovo offers some solutions ([osput][1], [tsmcli][2]) but each of them comes with their own set of compatibility and functional issues.

## Lenovo RPCs

A list of RPC calls for Lenovo servers has been curated by studying and examining the IPMI Web interface. They can be very useful for debugging, or for one-off uses where `bmcmanager` commands are not enough.

> NOTE: The commands have been tested with TSM version `4.92.903` and newer, but most of them should work in previous versions as well.

List known Lenovo RPC calls, along with a short description for each:

```bash
$ bmcmanager lenovo rpc list
```

> NOTE: This list is not exhaustive.

You can call any RPC like so:

```bash
$ bmcmanager lenovo rpc do --help
$ bmcmanager lenovo rpc do lar0510 --rpc getanalysedsel
```

[1]: https://support.lenovo.com/gr/en/downloads/ds101716
[2]: https://support.lenovo.com/us/en/downloads/ds101157
