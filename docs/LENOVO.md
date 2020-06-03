# Lenovo

Lenovo Thinkservers expose an ASP.NET REST API for performing most of their management tasks over a CLI.

Apart from the generic management commands that use the IPMI interface, we use this REST API to speed up the management process. Lenovo offers some solutions ([osput][1], [tsmcli][2]) but each of them comes with their own set of compatibility and functional issues.

## Extra commands

- `ipmi-logs-analyzed`: Retrieve SEL, with decoded OEM entries.
- `get-disks`: Retrieve disks, as read by the IPMI interface (also `check-disks`).
- `system-ram`: Get system RAM, as read by the IPMI interface (also `check-ram`).
- `lock-power-switch`: Lock power button, also `unlock-power-switch`.
- `lenovo-rpc`: Make a raw RPC call, see next section.
- `image-info`: Read firmware versions of all machine components.

## List of API calls

These are useful for debugging, or when our commands are not enough. You can call these like so:

```bash
$ bcmanager lenovo-rpc $SERVER --rpc $RPC_NAME --indent 4
```

This list is not exhaustive, and comes from reverse-engineering the Web UI and the `tsmcli` tool. These are for TSM version `4.92.903`, but most of them should work with other versions as well.

The Response object names are useful for cross-referencing the Javascript of the Web UI.

| RPC Name           | Description                                 | Response Object Name                   |
| ------------------ | ------------------------------------------- | -------------------------------------- |
| `getanalysedsel`   | Retrieve SEL, with OEM entries decoded.     | WEBVAR_JSONVAR_HL_GETANALYSEDSEL       |
| `getsysteminfo`    | BIOS version, Serial number, Model          | WEBVAR_JSONVAR_GETSYSTEMINFO           |
| `hoststatus`       | Host health                                 | WEBVAR_JSONVAR_HL_SYSTEM_STATE         |
| `getallsensors`    | Get status of all IPMI sensors              | WEBVAR_JSONVAR_HL_GETALLSENSORS        |
| `getuidled`        | Get identify LED status                     | WEBVAR_JSONVAR_HL_LED_IDENTIFY_STATE   |
| `gethealthledinfo` | Get health LED status                       | WEBVAR_JSONVAR_GETHEALTHLEDINFO        |
| `getalllancfg`     | Get network information for IPMI interfaces | WEBVAR_JSONVAR_GETALLNETWORKCFG        |
| `getdatetime`      | Get Server Time                             | WEBVAR_JSONVAR_GETDATETIME             |
| `gethddinfo`       | Connected Disks                             | WEBVAR_JSONVAR_GETINVDRIVEINFO         |
| `getalldimminfo`   | Connected DIMMs                             | WEBVAR_JSONVAR_INVENTORYGETALLDIMMINFO |
| `getfruinfo`       | Fetch all FRU devices                       | WEBVAR_JSONVAR_HL_GETALLFRUINFO        |
| `getallcpuinfo`    | Connected CPUs                              | WEBVAR_JSONVAR_INVENTORYGETALLCPUINFO  |
| `getimageinfo`     | Firmware versions                           | WEBVAR_JSONVAR_GETIMAGEINFO            |
| `getallpefcfg`     | Event Filters                               | WEBVAR_JSONVAR_HL_GETPEFTABLE          |
| `getauditlog`      | Audit log (connections)                     | WEBVAR_JSONVAR_GETAUDITLOG             |
| `getalluserinfo`   | IPMI users                                  | WEBVAR_JSONVAR_HL_GETALLUSERINFO       |
| `getldapcfg`       | LDAP auth configuration                     | WEBVAR_JSONVAR_GETLDAPCFG              |
| `getactivedircfg`  | Active Directory auth configuration         | WEBVAR_JSONVAR_GETLDAPCFG              |

[1]: https://support.lenovo.com/gr/en/downloads/ds101716
[2]: https://support.lenovo.com/us/en/downloads/ds101157
