# WP - Werewolf Protocol

Werewolf Protocol (WP in the context) defines ways for server and clients to communicate.

> For detailed gamerule, please refer to [`README.md`](../../README.md) in thr root directory.

Modules in the package are:

* `api.py`: provides an interface to send, receive and decode the data;
* `utils.py`: defines global variables in the module.

## `api.py`

`api.py` contains class `ChunckedData`, which use `json` module to encode the data and `gzip` module to compress the data. `recv()` function is used to receive such data and rebuild the `ChunckedData` packet.

## `utils.py`

Contents:

* `py2`: Version of the Python environment.
* `_packetType`: Defines the different packets to be used.
* `_checkParam`: Defines the format of the packets.

## Testing

The module use `pytest` to run the testcase. Execute `pytest` in the package directory to start a test.