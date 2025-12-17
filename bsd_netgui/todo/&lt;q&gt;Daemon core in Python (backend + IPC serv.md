
# <q>Daemon core in Python (backend + IPC server).

Small rc.d shell script to start/stop it properly on FreeBSD.</q> can you explain me roadmap to do this with an extensive todo list with steps

Start by treating the daemon as its own mini‑project, then bolt the rc.d wrapper and GUI on top.

## Phase 1 – Prep and repo layout

- [ ] Create a dedicated branch or fork for the daemon refactor, e.g. `daemon-backend`.
- [ ] Decide package layout, for example:
    - `bsd_netgui/`
        - `backend/` (pure logic, no GUI)
        - `ipc/` (Unix socket server + client helpers)
        - `daemon.py` (entry point)
        - `cli.py` (simple test client)
- [ ] Ensure Python 3 and needed libs are in `requirements.txt` (or `pyproject.toml`).


## Phase 2 – Isolate backend logic

Goal: backend that has zero GUI imports.

- [ ] Identify all network‑related logic currently inside GUI / wxPython classes:
    - Scanning, connecting, disconnecting.
    - Status polling, listing profiles, reading configs.
- [ ] Create `bsd_netgui/backend/core.py` with a clean API:
    - [ ] `scan_networks() -> list[dict]`
    - [ ] `connect(profile_name: str) -> bool / dict`
    - [ ] `disconnect()`
    - [ ] `get_status() -> dict`
    - [ ] `list_profiles() -> list[dict]`
- [ ] Move existing logic into these functions/classes.
- [ ] Add minimal tests or a quick driver:
    - [ ] `python -m bsd_netgui.backend.core` runs a few basic actions and prints JSON.


## Phase 3 – Design the IPC protocol

Use Unix domain socket + JSON.

- [ ] Decide on socket path (configurable), e.g. `/var/run/bsd_netd.sock` (for system service) or `$XDG_RUNTIME_DIR/bsd_netd.sock` (per user).
- [ ] Define request/response JSON format, e.g.:
    - Request:

```json
{ "id": 1, "cmd": "scan", "params": {} }
```

    - Response (success):

```json
{ "id": 1, "ok": true, "result": [ ... ] }
```

    - Response (error):

```json
{ "id": 1, "ok": false, "error": "message" }
```

- [ ] Enumerate commands:
    - `"scan"`, `"status"`, `"connect"`, `"disconnect"`, `"list_profiles"`, `"reload_config"`…


## Phase 4 – Implement the Python daemon

- [ ] Create `bsd_netgui/ipc/server.py`:
    - [ ] Opens a Unix socket (e.g. with `socket.AF_UNIX`, `SOCK_STREAM`).
    - [ ] Accepts connections in a loop (single‑threaded or simple thread per client).
    - [ ] For each request:
        - Read a line / length‑prefixed JSON.
        - Parse JSON, route `cmd` to backend `core` functions.
        - Catch exceptions and return an `"ok": false` error.
- [ ] Create `bsd_netgui/daemon.py`:
    - [ ] `main()`:
        - Parses command‑line options: `--socket-path`, `--log-file`, `--foreground`.
        - Initializes logging.
        - Starts `ipc.server` main loop.
    - [ ] Ensure it exits cleanly on SIGTERM (FreeBSD will send this from rc.d).
- [ ] Add a setuptools / entry‑point or just make it runnable:

```sh
python -m bsd_netgui.daemon --socket-path=/var/run/bsd_netd.sock
```


## Phase 5 – Implement a tiny IPC client (for testing \& GUI)

- [ ] Create `bsd_netgui/ipc/client.py`:
    - [ ] Helper function `call(cmd, params=None, socket_path=...) -> dict`:
        - Connects to Unix socket.
        - Sends JSON request.
        - Waits for JSON reply.
        - Returns `result` or raises on `"ok": false`.
- [ ] Create `bsd_netgui/cli.py`:
    - [ ] Simple CLI tool:

```sh
python -m bsd_netgui.cli scan
python -m bsd_netgui.cli status
python -m bsd_netgui.cli connect <profile>
```

    - [ ] Uses `ipc.client.call()` under the hood.
- [ ] Verify backend + IPC fully work **without** GUI.


## Phase 6 – Integrate wxPython GUI with the daemon

- [ ] In GUI code, remove direct imports of backend modules.
- [ ] Replace direct calls with IPC:
    - [ ] Instead of `backend.scan_networks()`, call `ipc.client.call("scan")`.
    - [ ] Map responses into your panel models.
- [ ] Handle async operations:
    - [ ] For long‑running operations (scan), call IPC from a worker thread or timer, then update UI safely on the main thread.
- [ ] Add GUI error handling for:
    - Daemon not running → show “service offline” indicator.
    - IPC timeouts → show retry / error toast.


## Phase 7 – FreeBSD rc.d integration

### 7.1. Python “service” command

Decide on install path, e.g. `/usr/local/bin/bsd_netd`:

- [ ] Installable entry script (via setup or simple copy) that does:

```sh
#!/bin/sh
exec /usr/local/bin/python3 -m bsd_netgui.daemon "$@"
```


### 7.2. rc.d script

- [ ] Create `/usr/local/etc/rc.d/bsd_netd` (mode 755, `root:wheel`), something like:

```sh
#!/bin/sh
#
# PROVIDE: bsd_netd
# REQUIRE: NETWORKING
# KEYWORD: shutdown

. /etc/rc.subr

name="bsd_netd"
rcvar=bsd_netd_enable

command="/usr/local/bin/bsd_netd"
pidfile="/var/run/${name}.pid"
command_args="--socket-path=/var/run/bsd_netd.sock --log-file=/var/log/bsd_netd.log"

load_rc_config $name
: ${bsd_netd_enable:="NO"}

run_rc_command "$1"
```

- [ ] Enable it in `rc.conf`:

```sh
sudo sysrc bsd_netd_enable=YES
```

- [ ] Start/stop for testing:

```sh
sudo service bsd_netd start
sudo service bsd_netd status
sudo service bsd_netd stop
```


## Phase 8 – Hardening \& polish

- [ ] Run daemon as unprivileged user:
    - [ ] Create a user, e.g. `bsdnetd`.
    - [ ] In rc.d: add `bsd_netd_user="bsdnetd"` and adjust socket/log dirs’ ownership.
- [ ] Logging:
    - [ ] Use Python `logging` to log to a file (e.g. `/var/log/bsd_netd.log`) and maybe syslog.
- [ ] Config file:
    - [ ] Add `bsd_netgui/config.py`, read from `/usr/local/etc/bsd_netd.conf` or `$HOME/.config/bsd_netd/config.toml`.
    - [ ] Allow overriding socket path, log path, default interface, etc.
- [ ] Timeouts and resilience:
    - [ ] Add timeouts on IPC client calls so GUI never hangs indefinitely.
    - [ ] Handle broken sockets gracefully (e.g. daemon restarted).


## Phase 9 – Documentation and packaging

- [ ] Document IPC commands and JSON schema in `docs/ipc.md`.
- [ ] Document how to:
    - Enable and control the daemon (`service bsd_netd start`…).
    - Use CLI (`bsd-net-cli scan` etc.).
    - Point the GUI at a custom socket if needed.
- [ ] If you plan to package as a FreeBSD port:
    - [ ] Add `USES=python` and install:
        - Python package into `SITE_PACKAGES`.
        - `/usr/local/bin/bsd_netd` script.
        - `/usr/local/etc/rc.d/bsd_netd` file.

***

If you want, next step can be a concrete minimal example of `ipc/server.py` in Python (just a few dozen lines) so you can start coding from a working skeleton rather than from scratch.
<span style="display:none">[^1][^2][^3]</span>

<div align="center">⁂</div>

[^1]: https://man.freebsd.org/cgi/man.cgi?query=rc\&apropos=0\&sektion=8\&manpath=FreeBSD+12.1-RELEASE\&arch=default\&format=html

[^2]: https://docs.freebsd.org/en/articles/rc-scripting/

[^3]: https://www.ipnom.com/FreeBSD-Man-Pages/rc.d.8.html

