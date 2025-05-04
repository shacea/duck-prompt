[![Documentation Status](https://readthedocs.org/projects/asyncssh/badge/?version=latest)](https://asyncssh.readthedocs.io/en/latest/?badge=latest)[![AsyncSSH PyPI Project](https://img.shields.io/pypi/v/asyncssh.svg)](https://pypi.python.org/pypi/asyncssh/)

# AsyncSSH: Asynchronous SSH for Python [¶](https://asyncssh.readthedocs.io/en/latest/#asyncssh-asynchronous-ssh-for-python "Link to this heading")

AsyncSSH is a Python package which provides an asynchronous client and
server implementation of the SSHv2 protocol on top of the Python 3.6+
asyncio framework.

```
import asyncio, asyncssh, sys

async def run_client():
    async with asyncssh.connect('localhost') as conn:
        result = await conn.run('echo "Hello!"', check=True)
        print(result.stdout, end='')

try:
    asyncio.get_event_loop().run_until_complete(run_client())
except (OSError, asyncssh.Error) as exc:
    sys.exit('SSH connection failed: ' + str(exc))

```

Check out the [examples](http://asyncssh.readthedocs.io/en/stable/#client-examples) to get started!

## Features [¶](https://asyncssh.readthedocs.io/en/latest/#features "Link to this heading")

- Full support for SSHv2, SFTP, and SCP client and server functions

  - Shell, command, and subsystem channels

  - Environment variables, terminal type, and window size

  - Direct and forwarded TCP/IP channels

  - OpenSSH-compatible direct and forwarded UNIX domain socket channels

  - OpenSSH-compatible TUN/TAP channels and packet forwarding

  - Local and remote TCP/IP port forwarding

  - Local and remote UNIX domain socket forwarding

  - Dynamic TCP/IP port forwarding via SOCKS

  - X11 forwarding support on both the client and the server

  - SFTP protocol version 3 with OpenSSH extensions

    - Experimental support for SFTP versions 4-6, when requested

  - SCP protocol support, including third-party remote to remote copies

- Multiple simultaneous sessions on a single SSH connection

- Multiple SSH connections in a single event loop

- Byte and string based I/O with settable encoding

- A variety of [key exchange](http://asyncssh.readthedocs.io/en/stable/api.html#key-exchange-algorithms), [encryption](http://asyncssh.readthedocs.io/en/stable/api.html#encryption-algorithms), and [MAC](http://asyncssh.readthedocs.io/en/stable/api.html#mac-algorithms) algorithms

  - Including post-quantum kex algorithms ML-KEM and SNTRUP

- Support for [gzip compression](http://asyncssh.readthedocs.io/en/stable/api.html#compression-algorithms)

  - Including OpenSSH variant to delay compression until after auth

- User and host-based public key, password, and keyboard-interactive
  authentication methods

- Many types and formats of [public keys and certificates](http://asyncssh.readthedocs.io/en/stable/api.html#public-key-support)

  - Including OpenSSH-compatible support for U2F and FIDO2 security keys

  - Including PKCS#11 support for accessing PIV security tokens

  - Including support for X.509 certificates as defined in RFC 6187

- Support for accessing keys managed by [ssh-agent](http://asyncssh.readthedocs.io/en/stable/api.html#ssh-agent-support) on UNIX systems

  - Including agent forwarding support on both the client and the server

- Support for accessing keys managed by PuTTY’s Pageant agent on Windows

- Support for accessing host keys via OpenSSH’s ssh-keysign

- OpenSSH-style [known_hosts file](http://asyncssh.readthedocs.io/en/stable/api.html#known-hosts) support

- OpenSSH-style [authorized_keys file](http://asyncssh.readthedocs.io/en/stable/api.html#authorized-keys) support

- Partial support for [OpenSSH-style configuration files](http://asyncssh.readthedocs.io/en/stable/api.html#config-file-support)

- Compatibility with OpenSSH “Encrypt then MAC” option for better security

- Time and byte-count based session key renegotiation

- Designed to be easy to extend to support new forms of key exchange,
  authentication, encryption, and compression algorithms

## License [¶](https://asyncssh.readthedocs.io/en/latest/#license "Link to this heading")

This package is released under the following terms:

> Copyright (c) 2013-2024 by Ron Frederick < [ronf@timeheart.net](mailto:ronf%40timeheart.net) \> and others.
>
> This program and the accompanying materials are made available under
> the terms of the Eclipse Public License v2.0 which accompanies this
> distribution and is available at:
>
> > [http://www.eclipse.org/legal/epl-2.0/](http://www.eclipse.org/legal/epl-2.0/)
>
> This program may also be made available under the following secondary
> licenses when the conditions for such availability set forth in the
> Eclipse Public License v2.0 are satisfied:
>
> > GNU General Public License, Version 2.0, or any later versions of
> > that license
>
> SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

For more information about this license, please see the [Eclipse\\
Public License FAQ](https://www.eclipse.org/legal/epl-2.0/faq.php).

## Prerequisites [¶](https://asyncssh.readthedocs.io/en/latest/#prerequisites "Link to this heading")

To use AsyncSSH 2.0 or later, you need the following:

- Python 3.6 or later

- cryptography (PyCA) 3.1 or later

## Installation [¶](https://asyncssh.readthedocs.io/en/latest/#installation "Link to this heading")

Install AsyncSSH by running:

> ```
> pip install asyncssh
>
> ```

### Optional Extras [¶](https://asyncssh.readthedocs.io/en/latest/#optional-extras "Link to this heading")

There are some optional modules you can install to enable additional
functionality:

- Install bcrypt from [https://pypi.python.org/pypi/bcrypt](https://pypi.python.org/pypi/bcrypt)
  if you want support for OpenSSH private key encryption.

- Install fido2 from [https://pypi.org/project/fido2](https://pypi.org/project/fido2) if you want support
  for key exchange and authentication with U2F/FIDO2 security keys.

- Install python-pkcs11 from [https://pypi.org/project/python-pkcs11](https://pypi.org/project/python-pkcs11) if
  you want support for accessing PIV keys on PKCS#11 security tokens.

- Install gssapi from [https://pypi.python.org/pypi/gssapi](https://pypi.python.org/pypi/gssapi) if you
  want support for GSSAPI key exchange and authentication on UNIX.

- Install liboqs from [https://github.com/open-quantum-safe/liboqs](https://github.com/open-quantum-safe/liboqs)
  if you want support for the OpenSSH post-quantum key exchange
  algorithms based on ML-KEM and SNTRUP.

- Install libsodium from [https://github.com/jedisct1/libsodium](https://github.com/jedisct1/libsodium)
  and libnacl from [https://pypi.python.org/pypi/libnacl](https://pypi.python.org/pypi/libnacl) if you have
  a version of OpenSSL older than 1.1.1b installed and you want
  support for Curve25519 key exchange, Ed25519 keys and certificates,
  or the Chacha20-Poly1305 cipher.

- Install libnettle from [http://www.lysator.liu.se/~nisse/nettle/](http://www.lysator.liu.se/~nisse/nettle/)
  if you want support for UMAC cryptographic hashes.

- Install pyOpenSSL from [https://pypi.python.org/pypi/pyOpenSSL](https://pypi.python.org/pypi/pyOpenSSL)
  if you want support for X.509 certificate authentication.

- Install pywin32 from [https://pypi.python.org/pypi/pywin32](https://pypi.python.org/pypi/pywin32) if you
  want support for using the Pageant agent or support for GSSAPI
  key exchange and authentication on Windows.

AsyncSSH defines the following optional PyPI extra packages to make it
easy to install any or all of these dependencies:

> bcrypt
>
> fido2
>
> gssapi
>
> libnacl
>
> pkcs11
>
> pyOpenSSL
>
> pywin32

For example, to install bcrypt, fido2, gssapi, libnacl, pkcs11, and
pyOpenSSL on UNIX, you can run:

> ```
> pip install 'asyncssh[bcrypt,fido2,gssapi,libnacl,pkcs11,pyOpenSSL]'
>
> ```

To install bcrypt, fido2, libnacl, pkcs11, pyOpenSSL, and pywin32 on
Windows, you can run:

> ```
> pip install 'asyncssh[bcrypt,fido2,libnacl,pkcs11,pyOpenSSL,pywin32]'
>
> ```

Note that you will still need to manually install the libsodium library
listed above for libnacl to work correctly and/or libnettle for UMAC
support. Unfortunately, since liboqs, libsodium, and libnettle are not
Python packages, they cannot be directly installed using pip.

### Installing the development branch [¶](https://asyncssh.readthedocs.io/en/latest/#installing-the-development-branch "Link to this heading")

If you would like to install the development branch of asyncssh directly
from Github, you can use the following command to do this:

> ```
> pip install git+https://github.com/ronf/asyncssh@develop
>
> ```

## Mailing Lists [¶](https://asyncssh.readthedocs.io/en/latest/#mailing-lists "Link to this heading")

Three mailing lists are available for AsyncSSH:

- [asyncssh-announce@googlegroups.com](http://groups.google.com/d/forum/asyncssh-announce): Project announcements

- [asyncssh-dev@googlegroups.com](http://groups.google.com/d/forum/asyncssh-dev): Development discussions

- [asyncssh-users@googlegroups.com](http://groups.google.com/d/forum/asyncssh-users): End-user discussions

# Client Examples [¶](https://asyncssh.readthedocs.io/en/latest/#client-examples "Link to this heading")

## Simple client [¶](https://asyncssh.readthedocs.io/en/latest/#simple-client "Link to this heading")

The following code shows an example of a simple SSH client which logs into
localhost and lists files in a directory named ‘abc’ under the user’s home
directory. The username provided is the logged in user, and the user’s
default SSH client keys or certificates are presented during authentication.
The server’s host key is checked against the user’s SSH known_hosts file and
the connection will fail if there’s no entry for localhost there or if the
key doesn’t match.

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         try:
>             result = await conn.run('ls abc', check=True)
>         except asyncssh.ProcessError as exc:
>             print(exc.stderr, end='')
>             print(f'Process exited with status {exc.exit_status}',
>                   file=sys.stderr)
>         else:
>             print(result.stdout, end='')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

This example shows using the [`SSHClientConnection`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection "asyncssh.SSHClientConnection") returned by
[`connect()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.connect "asyncssh.connect") as a context manager, so that the connection is
automatically closed when the end of the code block which opened it is
reached. However, if you need the connection object to live longer, you
can use “await” instead of “async with”:

> ```
> conn = await asyncssh.connect('localhost')
>
> ```

In this case, the application will need to close the connection explicitly
when done with it, and it is best to also wait for the close to complete.
This can be done with the following code from inside an async function:

> ```
> conn.close()
> await conn.wait_closed()
>
> ```

Only stdout is referenced this example, but output on stderr is also
collected as another attribute in the returned [`SSHCompletedProcess`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHCompletedProcess "asyncssh.SSHCompletedProcess")
object.

Shell and exec sessions default to an encoding of ‘utf-8’, so read and
write calls operate on strings by default. If you want to send and
receive binary data, you can set the encoding to [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") when the
session is opened to make read and write operate on bytes instead.
Alternate encodings can also be selected to change how strings are
converted to and from bytes.

To check against a different set of server host keys, they can be provided
in the known_hosts argument when the connection is opened:

> ```
> async with asyncssh.connect('localhost', known_hosts='my_known_hosts') as conn:
>
> ```

Server host key checking can be disabled by setting the known_hosts
argument to `None`, but that’s not recommended as it makes the
connection vulnerable to a man-in-the-middle attack.

To log in as a different remote user, the username argument can be
provided:

> ```
> async with asyncssh.connect('localhost', username='user123') as conn:
>
> ```

To use a different set of client keys for authentication, they can be
provided in the client_keys argument:

> ```
> async with asyncssh.connect('localhost', client_keys=['my_ssh_key']) as conn:
>
> ```

Password authentication can be used by providing a password argument:

> ```
> async with asyncssh.connect('localhost', password='secretpw') as conn:
>
> ```

Any of the arguments above can be combined together as needed. If client
keys and a password are both provided, either may be used depending
on what forms of authentication the server supports and whether the
authentication with them is successful.

## Callback example [¶](https://asyncssh.readthedocs.io/en/latest/#callback-example "Link to this heading")

AsyncSSH also provides APIs that use callbacks rather than “await” and “async
with”. Here’s the example above written using custom [`SSHClient`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClient "asyncssh.SSHClient") and
[`SSHClientSession`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientSession "asyncssh.SSHClientSession") subclasses:

> ```
> import asyncio, asyncssh, sys
> from typing import Optional
>
> class MySSHClientSession(asyncssh.SSHClientSession):
>     def data_received(self, data: str, datatype: asyncssh.DataType) -> None:
>         print(data, end='')
>
>     def connection_lost(self, exc: Optional[Exception]) -> None:
>         if exc:
>             print('SSH session error: ' + str(exc), file=sys.stderr)
>
> class MySSHClient(asyncssh.SSHClient):
>     def connection_made(self, conn: asyncssh.SSHClientConnection) -> None:
>         print(f'Connection made to {conn.get_extra_info('peername')[0]}.')
>
>     def auth_completed(self) -> None:
>         print('Authentication successful.')
>
> async def run_client() -> None:
>     conn, client = await asyncssh.create_connection(MySSHClient, 'localhost')
>
>     async with conn:
>         chan, session = await conn.create_session(MySSHClientSession, 'ls abc')
>         await chan.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

In cases where you don’t need to customize callbacks on the SSHClient class,
this code can be simplified somewhat to:

> ```
> import asyncio, asyncssh, sys
> from typing import Optional
>
> class MySSHClientSession(asyncssh.SSHClientSession):
>     def data_received(self, data: str, datatype: asyncssh.DataType) -> None:
>         print(data, end='')
>
>     def connection_lost(self, exc: Optional[Exception]) -> None:
>         if exc:
>             print('SSH session error: ' + str(exc), file=sys.stderr)
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         chan, session = await conn.create_session(MySSHClientSession, 'ls abc')
>         await chan.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

If you need to distinguish output going to stdout vs. stderr, that’s easy to
do with the following change:

> ```
> import asyncio, asyncssh, sys
> from typing import Optional
>
> class MySSHClientSession(asyncssh.SSHClientSession):
>     def data_received(self, data: str, datatype: asyncssh.DataType) -> None:
>         if datatype == asyncssh.EXTENDED_DATA_STDERR:
>             print(data, end='', file=sys.stderr)
>         else:
>             print(data, end='')
>
>     def connection_lost(self, exc: Optional[Exception]) -> None:
>         if exc:
>             print('SSH session error: ' + str(exc), file=sys.stderr)
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         chan, session = await conn.create_session(MySSHClientSession, 'ls abc')
>         await chan.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

## Interactive input [¶](https://asyncssh.readthedocs.io/en/latest/#interactive-input "Link to this heading")

The following example demonstrates sending interactive input to a remote
process. It executes the calculator program `bc` and performs some basic
math calculations. Note that it uses the [`create_process`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.create_process "asyncssh.SSHClientConnection.create_process") method rather than the [`run`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.run "asyncssh.SSHClientConnection.run") method. This starts the process but doesn’t wait
for it to exit, allowing interaction with it.

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         async with conn.create_process('bc') as process:
>             for op in ['2+2', '1*2*3*4', '2^32']:
>                 process.stdin.write(op + '\n')
>                 result = await process.stdout.readline()
>                 print(op, '=', result, end='')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

When run, this program should produce the following output:

> ```
> 2+2 = 4
> 1*2*3*4 = 24
> 2^32 = 4294967296
>
> ```

## I/O redirection [¶](https://asyncssh.readthedocs.io/en/latest/#i-o-redirection "Link to this heading")

The following example shows how to pass a fixed input string to a remote
process and redirect the resulting output to the local file ‘/tmp/stdout’.
Input lines containing 1, 2, and 3 are passed into the ‘tail -r’ command
and the output written to ‘/tmp/stdout’ should contain the reversed lines
3, 2, and 1:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         await conn.run('tail -r', input='1\n2\n3\n', stdout='/tmp/stdout')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

The `stdin`, `stdout`, and `stderr` arguments support redirecting
to a variety of locations include local files, pipes, and sockets as
well as [`SSHReader`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHReader "asyncssh.SSHReader") or [`SSHWriter`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHWriter "asyncssh.SSHWriter") objects associated with
other remote SSH processes. Here’s an example of piping stdout from a
local process to a remote process:

> ```
> import asyncio, asyncssh, subprocess, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         local_proc = subprocess.Popen(r'echo "1\n2\n3"', shell=True,
>                                       stdout=subprocess.PIPE)
>         remote_result = await conn.run('tail -r', stdin=local_proc.stdout)
>         print(remote_result.stdout, end='')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

Here’s an example of piping one remote process to another:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         proc1 = await conn.create_process(r'echo "1\n2\n3"')
>         proc2_result = await conn.run('tail -r', stdin=proc1.stdout)
>         print(proc2_result.stdout, end='')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

In this example both remote processes are running on the same SSH
connection, but this redirection can just as easily be used between
SSH sessions associated with connections going to different servers.

## Checking exit status [¶](https://asyncssh.readthedocs.io/en/latest/#checking-exit-status "Link to this heading")

The following example shows how to test the exit status of a remote process:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         result = await conn.run('ls abc')
>
>         if result.exit_status == 0:
>             print(result.stdout, end='')
>         else:
>             print(result.stderr, end='', file=sys.stderr)
>             print(f'Program exited with status {result.exit_status}',
>                   file=sys.stderr)
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

If an exit signal is received, the exit status will be set to -1 and exit
signal information is provided in the `exit_signal` attribute of the
returned [`SSHCompletedProcess`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHCompletedProcess "asyncssh.SSHCompletedProcess").

If the `check` argument in [`run`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.run "asyncssh.SSHClientConnection.run") is set
to `True`, any abnormal exit will raise a [`ProcessError`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.ProcessError "asyncssh.ProcessError") exception
instead of returning an [`SSHCompletedProcess`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHCompletedProcess "asyncssh.SSHCompletedProcess").

## Running multiple clients [¶](https://asyncssh.readthedocs.io/en/latest/#running-multiple-clients "Link to this heading")

The following example shows how to run multiple clients in parallel and
process the results when all of them have completed:

> ```
> import asyncio, asyncssh
>
> async def run_client(host, command: str) -> asyncssh.SSHCompletedProcess:
>     async with asyncssh.connect(host) as conn:
>         return await conn.run(command)
>
> async def run_multiple_clients() -> None:
>     # Put your lists of hosts here
>     hosts = 5 * ['localhost']
>
>     tasks = (run_client(host, 'ls abc') for host in hosts)
>     results = await asyncio.gather(*tasks, return_exceptions=True)
>
>     for i, result in enumerate(results, 1):
>         if isinstance(result, Exception):
>             print(f'Task {i} failed: {result}')
>         elif result.exit_status != 0:
>             print(f'Task {i} exited with status {result.exit_status}:')
>             print(result.stderr, end='')
>         else:
>             print(f'Task {i} succeeded:')
>             print(result.stdout, end='')
>
>         print(75*'-')
>
> asyncio.run(run_multiple_clients())
>
> ```

Results could be processed as they became available by setting up a
loop which repeatedly called [`asyncio.wait()`](https://docs.python.org/3/library/asyncio-task.html#asyncio.wait "(in Python v3.13)") instead of calling
[`asyncio.gather()`](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather "(in Python v3.13)").

## Setting environment variables [¶](https://asyncssh.readthedocs.io/en/latest/#setting-environment-variables "Link to this heading")

The following example demonstrates setting environment variables
for the remote session and displaying them by executing the ‘env’
command.

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         result = await conn.run('env', env={'LANG': 'en_GB',
>                                             'LC_COLLATE': 'C'})
>         print(result.stdout, end='')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

Any number of environment variables can be passed in the dictionary
given to [`create_session()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.create_session "asyncssh.SSHClientConnection.create_session").
Note that SSH servers may restrict which environment variables (if any)
are accepted, so this feature may require setting options on the SSH
server before it will work.

## Setting terminal information [¶](https://asyncssh.readthedocs.io/en/latest/#setting-terminal-information "Link to this heading")

The following example demonstrates setting the terminal type and size
passed to the remote session.

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         result = await conn.run('echo $TERM; stty size',
>                                 term_type='xterm-color',
>                                 term_size=(80, 24))
>         print(result.stdout, end='')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

Note that this will cause AsyncSSH to request a pseudo-tty from the
server. When a pseudo-tty is used, the server will no longer send output
going to stderr with a different data type. Instead, it will be mixed
with output going to stdout (unless it is redirected elsewhere by the
remote command).

## Port forwarding [¶](https://asyncssh.readthedocs.io/en/latest/#port-forwarding "Link to this heading")

The following example demonstrates the client setting up a local TCP
listener on port 8080 and requesting that connections which arrive on
that port be forwarded across SSH to the server and on to port 80 on
`www.google.com`:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         listener = await conn.forward_local_port('', 8080, 'www.google.com', 80)
>         await listener.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

To listen on a dynamically assigned port, the client can pass in `0`
as the listening port. If the listener is successfully opened, the selected
port will be available via the [`get_port()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHListener.get_port "asyncssh.SSHListener.get_port")
method on the returned listener object:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         listener = await conn.forward_local_port('', 0, 'www.google.com', 80)
>         print(f'Listening on port {listener.get_port()}...')
>         await listener.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

The client can also request remote port forwarding from the server. The
following example shows the client requesting that the server listen on
port 8080 and that connections arriving there be forwarded across SSH
and on to port 80 on `localhost`:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         listener = await conn.forward_remote_port('', 8080, 'localhost', 80)
>         await listener.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

To limit which connections are accepted or dynamically select where to
forward traffic to, the client can implement their own session factory and
call `forward_connection()`
on the connections they wish to forward and raise an error on those they
wish to reject:

> ```
> import asyncio, asyncssh, sys
> from functools import partial
> from typing import Awaitable
>
> def connection_requested(conn: asyncssh.SSHClientConnection, orig_host: str,
>                          orig_port: int) -> Awaitable[asyncssh.SSHForwarder]:
>     if orig_host in ('127.0.0.1', '::1'):
>         return conn.forward_connection('localhost', 80)
>     else:
>         raise asyncssh.ChannelOpenError(
>             asyncssh.OPEN_ADMINISTRATIVELY_PROHIBITED,
>             'Connections only allowed from localhost')
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         listener = await conn.create_server(
>             partial(connection_requested, conn), '', 8080)
>         await listener.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

Just as with local listeners, the client can request remote port forwarding
from a dynamic port by passing in `0` as the listening port and then call
[`get_port()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHListener.get_port "asyncssh.SSHListener.get_port") on the returned listener to
determine which port was selected.

## Direct TCP connections [¶](https://asyncssh.readthedocs.io/en/latest/#direct-tcp-connections "Link to this heading")

The client can also ask the server to open a TCP connection and directly
send and receive data on it by using the [`create_connection()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.create_connection "asyncssh.SSHClientConnection.create_connection") method on the
[`SSHClientConnection`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection "asyncssh.SSHClientConnection") object. In this example, a connection is
attempted to port 80 on `www.google.com` and an HTTP HEAD request is
sent for the document root.

Note that unlike sessions created with [`create_session()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.create_session "asyncssh.SSHClientConnection.create_session"), the I/O on these connections defaults
to sending and receiving bytes rather than strings, allowing arbitrary
binary data to be exchanged. However, this can be changed by setting
the encoding to use when the connection is created.

> ```
> import asyncio, asyncssh, sys
> from typing import Optional
>
> class MySSHTCPSession(asyncssh.SSHTCPSession):
>     def data_received(self, data: bytes, datatype: asyncssh.DataType) -> None:
>         # We use sys.stdout.buffer here because we're writing bytes
>         sys.stdout.buffer.write(data)
>
>     def connection_lost(self, exc: Optional[Exception]) -> None:
>         if exc:
>             print('Direct connection error:', str(exc), file=sys.stderr)
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         chan, session = await conn.create_connection(MySSHTCPSession,
>                                                      'www.google.com', 80)
>
>         # By default, TCP connections send and receive bytes
>         chan.write(b'HEAD / HTTP/1.0\r\n\r\n')
>         chan.write_eof()
>
>         await chan.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

To use the streams API to open a direct connection, you can use
[`open_connection`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.open_connection "asyncssh.SSHClientConnection.open_connection") instead of
[`create_connection`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.create_connection "asyncssh.SSHClientConnection.create_connection"):

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         reader, writer = await conn.open_connection('www.google.com', 80)
>
>         # By default, TCP connections send and receive bytes
>         writer.write(b'HEAD / HTTP/1.0\r\n\r\n')
>         writer.write_eof()
>
>         # We use sys.stdout.buffer here because we're writing bytes
>         response = await reader.read()
>         sys.stdout.buffer.write(response)
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

## Forwarded TCP connections [¶](https://asyncssh.readthedocs.io/en/latest/#forwarded-tcp-connections "Link to this heading")

The client can also directly process data from incoming TCP connections
received on the server. The following example demonstrates the client
requesting that the server listen on port 8888 and forward any received
connections back to it over SSH. It then has a simple handler which
echoes any data it receives back to the sender.

As in the direct TCP connection example above, the default would be to
send and receive bytes on this connection rather than strings, but here
we set the encoding explicitly so all data is sent and received as strings:

> ```
> import asyncio, asyncssh, sys
>
> class MySSHTCPSession(asyncssh.SSHTCPSession):
>     def connection_made(self, chan: asyncssh.SSHTCPChannel) -> None:
>         self._chan = chan
>
>     def data_received(self, data: bytes, datatype: asyncssh.DataType):
>         self._chan.write(data)
>
> def connection_requested(orig_host: str,
>                          orig_port: int) -> asyncssh.SSHTCPSession:
>     print(f'Connection received from {orig_host}, port {orig_port}')
>     return MySSHTCPSession()
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         server = await conn.create_server(connection_requested, '', 8888,
>                                           encoding='utf-8')
>
>         if server:
>             await server.wait_closed()
>         else:
>             print('Listener couldn\'t be opened.', file=sys.stderr)
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

To use the streams API to open a listening connection, you can use
[`start_server`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.start_server "asyncssh.SSHClientConnection.start_server") instead
of [`create_server`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection.create_server "asyncssh.SSHClientConnection.create_server"):

> ```
> import asyncio, asyncssh, sys
>
> async def handle_connection(reader, writer):
>     while not reader.at_eof():
>         data = await reader.read(8192)
>         writer.write(data)
>
>     writer.close()
>
> def connection_requested(orig_host, orig_port):
>     print(f'Connection received from {orig_host}, port {orig_port}')
>     return handle_connection
>
> async def run_client():
>     async with asyncssh.connect('localhost') as conn:
>         server = await conn.start_server(connection_requested, '', 8888,
>                                          encoding='utf-8')
>         await server.wait_closed()
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH connection failed: ' + str(exc))
>
> ```

## SFTP client [¶](https://asyncssh.readthedocs.io/en/latest/#sftp-client "Link to this heading")

AsyncSSH also provides SFTP support. The following code shows an example
of starting an SFTP client and requesting the download of a file:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     async with asyncssh.connect('localhost') as conn:
>         async with conn.start_sftp_client() as sftp:
>             await sftp.get('example.txt')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SFTP operation failed: ' + str(exc))
>
> ```

To recursively download a directory, preserving access and modification
times and permissions on the files, the preserve and recurse arguments
can be included:

> ```
> await sftp.get('example_dir', preserve=True, recurse=True)
>
> ```

Wild card pattern matching is supported by the [`mget`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPClient.mget "asyncssh.SFTPClient.mget"),
[`mput`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPClient.mput "asyncssh.SFTPClient.mput"), and [`mcopy`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPClient.mcopy "asyncssh.SFTPClient.mcopy") methods.
The following downloads all files with extension “txt”:

> ```
> await sftp.mget('*.txt')
>
> ```

See the [`SFTPClient`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPClient "asyncssh.SFTPClient") documentation for the full list of available
actions.

## SCP client [¶](https://asyncssh.readthedocs.io/en/latest/#scp-client "Link to this heading")

AsyncSSH also supports SCP. The following code shows an example of
downloading a file via SCP:

> ```
> import asyncio, asyncssh, sys
>
> async def run_client() -> None:
>     await asyncssh.scp('localhost:example.txt', '.')
>
> try:
>     asyncio.run(run_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SFTP operation failed: ' + str(exc))
>
> ```

To upload a file to a remote system, host information can be specified for
the destination instead of the source:

> ```
> await asyncssh.scp('example.txt', 'localhost:')
>
> ```

If the destination path includes a file name, that name will be used instead
of the original file name when performing the copy. For instance:

> ```
> await asyncssh.scp('example.txt', 'localhost:example2.txt')
>
> ```

If the destination path refers to a directory, the origin file name
will be preserved, but it will be copied into the requested directory.

Wild card patterns are also supported on local source paths. For instance,
the following copies all files with extension “txt”:

> ```
> await asyncssh.scp('*.txt', 'localhost:')
>
> ```

When copying files from a remote system, any wild card expansion is the
responsibility of the remote SCP program or the shell which starts it.

Similar to SFTP, SCP also supports options for recursively copying a
directory and preserving modification times and permissions on files
using the preserve and recurse arguments:

> ```
> await asyncssh.scp('example_dir', 'localhost:', preserve=True, recurse=True)
>
> ```

In addition to the `'host:path'` syntax for source and destination paths,
a tuple of the form `(host, path)` is also supported. A non-default port
can be specified by replacing `host` with `(host, port)`, resulting in
something like:

> ```
> await asyncssh.scp((('localhost', 8022), 'example.txt'), '.')
>
> ```

An already open [`SSHClientConnection`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHClientConnection "asyncssh.SSHClientConnection") can also be passed as the host:

> ```
> async with asyncssh.connect('localhost') as conn:
>     await asyncssh.scp((conn, 'example.txt'), '.')
>
> ```

Multiple file patterns can be copied to the same destination by making the
source path argument a list. Source paths in this list can be a mixture
of local and remote file references and the destination path can be
local or remote, but one or both of source and destination must be remote.
Local to local copies are not supported.

See the [`scp()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.scp "asyncssh.scp") function documentation for the complete list of
available options.

# Server Examples [¶](https://asyncssh.readthedocs.io/en/latest/#server-examples "Link to this heading")

## Simple server [¶](https://asyncssh.readthedocs.io/en/latest/#simple-server "Link to this heading")

The following code shows an example of a simple SSH server which listens
for connections on port 8022, does password authentication, and prints
a message when users authenticate successfully and start a shell.

Shell and exec sessions default to an encoding of ‘utf-8’, so read and
write calls operate on strings by default. If you want to send and
receive binary data, you can set the encoding to [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") when the
session is opened to make read and write operate on bytes instead.
Alternate encodings can also be selected to change how strings are
converted to and from bytes.

> ```
> # To run this program, the file ``ssh_host_key`` must exist with an SSH
> # private key in it to use as a server host key. An SSH host certificate
> # can optionally be provided in the file ``ssh_host_key-cert.pub``.
>
> import asyncio, asyncssh, bcrypt, sys
> from typing import Optional
>
> passwords = {'guest': b'',                # guest account with no password
>              'user123': bcrypt.hashpw(b'secretpw', bcrypt.gensalt()),
>             }
>
> def handle_client(process: asyncssh.SSHServerProcess) -> None:
>     username = process.get_extra_info('username')
>     process.stdout.write(f'Welcome to my SSH server, {username}!\n')
>     process.exit(0)
>
> class MySSHServer(asyncssh.SSHServer):
>     def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
>         peername = conn.get_extra_info('peername')[0]
>         print(f'SSH connection received from {peername}.')
>
>     def connection_lost(self, exc: Optional[Exception]) -> None:
>         if exc:
>             print('SSH connection error: ' + str(exc), file=sys.stderr)
>         else:
>             print('SSH connection closed.')
>
>     def begin_auth(self, username: str) -> bool:
>         # If the user's password is the empty string, no auth is required
>         return passwords.get(username) != b''
>
>     def password_auth_supported(self) -> bool:
>         return True
>
>     def validate_password(self, username: str, password: str) -> bool:
>         if username not in passwords:
>             return False
>         pw = passwords[username]
>         if not password and not pw:
>             return True
>         return bcrypt.checkpw(password.encode('utf-8'), pw)
>
> async def start_server() -> None:
>     await asyncssh.create_server(MySSHServer, '', 8022,
>                                  server_host_keys=['ssh_host_key'],
>                                  process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

To authenticate with SSH client keys or certificates, the server would
look something like the following. Client and certificate authority
keys for each user need to be placed in a file matching the username in
a directory called `authorized_keys`.

> ```
> import asyncio, asyncssh, sys
>
> def handle_client(process: asyncssh.SSHServerProcess) -> None:
>     username = process.get_extra_info('username')
>     process.stdout.write(f'Welcome to my SSH server, {username}!\n')
>     process.exit(0)
>
> class MySSHServer(asyncssh.SSHServer):
>     def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
>         self._conn = conn
>
>     def begin_auth(self, username: str) -> bool:
>         try:
>             self._conn.set_authorized_keys(f'authorized_keys/{username}')
>         except OSError:
>             pass
>
>         return True
>
> async def start_server() -> None:
>     await asyncssh.create_server(MySSHServer, '', 8022,
>                                  server_host_keys=['ssh_host_key'],
>                                  process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

It is also possible to use a single authorized_keys file for all users.
This is common when using certificates, as AsyncSSH can automatically
enforce that the certificates presented have a principal in them which
matches the username. In this case, a custom [`SSHServer`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHServer "asyncssh.SSHServer") subclass
is no longer required, and so the [`listen()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.listen "asyncssh.listen") function can be used in
place of [`create_server()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.create_server "asyncssh.create_server").

> ```
> import asyncio, asyncssh, sys
>
> def handle_client(process: asyncssh.SSHServerProcess) -> None:
>     username = process.get_extra_info('username')
>     process.stdout.write(f'Welcome to my SSH server, {username}!\n')
>     process.exit(0)
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Simple server with input [¶](https://asyncssh.readthedocs.io/en/latest/#simple-server-with-input "Link to this heading")

The following example demonstrates reading input in a server session.
It adds a column of numbers, displaying the total when it receives EOF.

> ```
> import asyncio, asyncssh, sys
>
> async def handle_client(process: asyncssh.SSHServerProcess) -> None:
>     process.stdout.write('Enter numbers one per line, or EOF when done:\n')
>
>     total = 0
>
>     try:
>         async for line in process.stdin:
>             line = line.rstrip('\n')
>             if line:
>                 try:
>                     total += int(line)
>                 except ValueError:
>                     process.stderr.write(f'Invalid number: {line}\n')
>     except asyncssh.BreakReceived:
>         pass
>
>     process.stdout.write(f'Total = {total}\n')
>     process.exit(0)
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Callback example [¶](https://asyncssh.readthedocs.io/en/latest/#id14 "Link to this heading")

Here’s an example of the server above written using callbacks in
custom [`SSHServer`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHServer "asyncssh.SSHServer") and [`SSHServerSession`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHServerSession "asyncssh.SSHServerSession") subclasses.

> ```
> import asyncio, asyncssh, sys
>
> class MySSHServerSession(asyncssh.SSHServerSession):
>     def __init__(self):
>         self._input = ''
>         self._total = 0
>
>     def connection_made(self, chan: asyncssh.SSHServerChannel):
>         self._chan = chan
>
>     def shell_requested(self) -> bool:
>         return True
>
>     def session_started(self) -> None:
>         self._chan.write('Enter numbers one per line, or EOF when done:\n')
>
>     def data_received(self, data: str, datatype: asyncssh.DataType) -> None:
>         self._input += data
>
>         lines = self._input.split('\n')
>         for line in lines[:-1]:
>             try:
>                 if line:
>                     self._total += int(line)
>             except ValueError:
>                 self._chan.write_stderr(f'Invalid number: {line}\n')
>
>         self._input = lines[-1]
>
>     def eof_received(self) -> bool:
>         self._chan.write(f'Total = {self._total}\n')
>         self._chan.exit(0)
>         return False
>
>     def break_received(self, msec: int) -> bool:
>         return self.eof_received()
>
>     def soft_eof_received(self) -> None:
>         self.eof_received()
>
> class MySSHServer(asyncssh.SSHServer):
>     def session_requested(self) -> asyncssh.SSHServerSession:
>         return MySSHServerSession()
>
> async def start_server() -> None:
>     await asyncssh.create_server(MySSHServer, '', 8022,
>                                  server_host_keys=['ssh_host_key'],
>                                  authorized_client_keys='ssh_user_ca')
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## I/O redirection [¶](https://asyncssh.readthedocs.io/en/latest/#id15 "Link to this heading")

The following shows an example of I/O redirection on the server side,
executing a process on the server with input and output redirected
back to the SSH client:

> ```
> import asyncio, asyncssh, subprocess, sys
>
> async def handle_client(process: asyncssh.SSHServerProcess) -> None:
>     bc_proc = subprocess.Popen('bc', shell=True, stdin=subprocess.PIPE,
>                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
>
>     await process.redirect(stdin=bc_proc.stdin, stdout=bc_proc.stdout,
>                            stderr=bc_proc.stderr)
>     await process.stdout.drain()
>     process.exit(0)
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Serving multiple clients [¶](https://asyncssh.readthedocs.io/en/latest/#serving-multiple-clients "Link to this heading")

The following is a slightly more complicated example showing how a
server can manage multiple simultaneous clients. It implements a
basic chat service, where clients can send messages to one other.

> ```
> import asyncio, asyncssh, sys
> from typing import List, cast
>
> class ChatClient:
>     _clients: List['ChatClient'] = []
>
>     def __init__(self, process: asyncssh.SSHServerProcess):
>         self._process = process
>
>     @classmethod
>     async def handle_client(cls, process: asyncssh.SSHServerProcess):
>         await cls(process).run()
>
>     async def readline(self) -> str:
>         return cast(str, self._process.stdin.readline())
>
>     def write(self, msg: str) -> None:
>         self._process.stdout.write(msg)
>
>     def broadcast(self, msg: str) -> None:
>         for client in self._clients:
>             if client != self:
>                 client.write(msg)
>
>     async def run(self) -> None:
>         self.write('Welcome to chat!\n\n')
>
>         self.write('Enter your name: ')
>         name = (await self.readline()).rstrip('\n')
>
>         self.write(f'\n{len(self._clients)} other users are connected.\n\n')
>
>         self._clients.append(self)
>         self.broadcast(f'*** {name} has entered chat ***\n')
>
>         try:
>             async for line in self._process.stdin:
>                 self.broadcast(f'{name}: {line}')
>         except asyncssh.BreakReceived:
>             pass
>
>         self.broadcast(f'*** {name} has left chat ***\n')
>         self._clients.remove(self)
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           process_factory=ChatClient.handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Line editing [¶](https://asyncssh.readthedocs.io/en/latest/#line-editing "Link to this heading")

When SSH clients request a pseudo-terminal, they generally default to
sending input a character at a time and expect the remote system to
provide character echo and line editing. To better support interactive
applications like the one above, AsyncSSH defaults to providing basic
line editing for server sessions which request a pseudo-terminal.

When this line editor is enabled, it defaults to delivering input to
the application a line at a time. Applications can switch between line
and character at a time input using the [`set_line_mode()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHLineEditorChannel.set_line_mode "asyncssh.SSHLineEditorChannel.set_line_mode") method. Also, when in line
mode, applications can enable or disable echoing of input using the
[`set_echo()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHLineEditorChannel.set_echo "asyncssh.SSHLineEditorChannel.set_echo") method. The
following code provides an example of this.

> ```
> import asyncio, asyncssh, sys
> from typing import cast
>
> async def handle_client(process: asyncssh.SSHServerProcess):
>     channel = cast(asyncssh.SSHLineEditorChannel, process.channel)
>
>     username = process.get_extra_info('username')
>     process.stdout.write(f'Welcome to my SSH server, {username}!\n\n')
>
>     channel.set_echo(False)
>     process.stdout.write('Tell me a secret: ')
>     secret = await process.stdin.readline()
>
>     channel.set_line_mode(False)
>     process.stdout.write('\nYour secret is safe with me! '
>                          'Press any key to exit...')
>     await process.stdin.read(1)
>
>     process.stdout.write('\n')
>     process.exit(0)
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Getting environment variables [¶](https://asyncssh.readthedocs.io/en/latest/#getting-environment-variables "Link to this heading")

The following example demonstrates reading environment variables set
by the client. It will show all of the variables set by the client,
or return an error if none are set. Note that SSH clients may restrict
which environment variables (if any) are sent by default, so you may
need to set options in the client to get it to do so.

> ```
> import asyncio, asyncssh, sys
>
> async def handle_client(process: asyncssh.SSHServerProcess) -> None:
>     if process.env:
>         keywidth = max(map(len, process.env.keys()))+1
>         process.stdout.write('Environment:\n')
>         for key, value in process.env.items():
>             process.stdout.write(f'  {key+":":{keywidth}} {value}\n')
>         process.exit(0)
>     else:
>         process.stderr.write('No environment sent.\n')
>         process.exit(1)
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Getting terminal information [¶](https://asyncssh.readthedocs.io/en/latest/#getting-terminal-information "Link to this heading")

The following example demonstrates reading the client’s terminal
type and window size, and handling window size changes during a
session.

> ```
> import asyncio, asyncssh, sys
>
> async def handle_client(process: asyncssh.SSHServerProcess) -> None:
>     width, height, pixwidth, pixheight = process.term_size
>
>     process.stdout.write(f'Terminal type: {process.term_type}, '
>                          f'size: {width}x{height}')
>     if pixwidth and pixheight:
>         process.stdout.write(f' ({pixwidth}x{pixheight} pixels)')
>     process.stdout.write('\nTry resizing your window!\n')
>
>     while not process.stdin.at_eof():
>         try:
>             await process.stdin.read()
>         except asyncssh.TerminalSizeChanged as exc:
>             process.stdout.write(f'New window size: {exc.width}x{exc.height}')
>             if exc.pixwidth and exc.pixheight:
>                 process.stdout.write(f' ({exc.pixwidth}'
>                                      f'x{exc.pixheight} pixels)')
>             process.stdout.write('\n')
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           process_factory=handle_client)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Port forwarding [¶](https://asyncssh.readthedocs.io/en/latest/#id16 "Link to this heading")

The following example demonstrates a server accepting port forwarding
requests from clients, but only when they are destined to port 80. When
such a connection is received, a connection is attempted to the requested
host and port and data is bidirectionally forwarded over SSH from the
client to this destination. Requests by the client to connect to any
other port are rejected.

> ```
> import asyncio, asyncssh, sys
>
> class MySSHServer(asyncssh.SSHServer):
>     def connection_requested(self, dest_host: str, dest_port: int,
>                              orig_host: str, orig_port: int) -> bool:
>         if dest_port == 80:
>             return True
>         else:
>             raise asyncssh.ChannelOpenError(
>                       asyncssh.OPEN_ADMINISTRATIVELY_PROHIBITED,
>                       'Only connections to port 80 are allowed')
>
> async def start_server() -> None:
>     await asyncssh.create_server(MySSHServer, '', 8022,
>                                  server_host_keys=['ssh_host_key'],
>                                  authorized_client_keys='ssh_user_ca')
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH server failed: ' + str(exc))
>
> loop.run_forever()
>
> ```

The server can also support forwarding inbound TCP connections back to
the client. The following example demonstrates a server which will accept
requests like this from clients, but only to listen on port 8080. When
such a connection is received, the client is notified and data is
bidirectionally forwarded from the incoming connection over SSH to the
client.

> ```
> import asyncio, asyncssh, sys
>
> class MySSHServer(asyncssh.SSHServer):
>     def server_requested(self, listen_host: str, listen_port: int) -> bool:
>         return listen_port == 8080
>
> async def start_server() -> None:
>     await asyncssh.create_server(MySSHServer, '', 8022,
>                                  server_host_keys=['ssh_host_key'],
>                                  authorized_client_keys='ssh_user_ca')
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH server failed: ' + str(exc))
>
> loop.run_forever()
>
> ```

## Direct TCP connections [¶](https://asyncssh.readthedocs.io/en/latest/#id17 "Link to this heading")

The server can also accept direct TCP connection requests from the client
and process the data on them itself. The following example demonstrates a
server which accepts requests to port 7 (the “echo” port) for any host and
echoes the data itself rather than forwarding the connection:

> ```
> import asyncio, asyncssh, sys
>
> class MySSHTCPSession(asyncssh.SSHTCPSession):
>     def connection_made(self, chan: asyncssh.SSHTCPChannel) -> None:
>         self._chan = chan
>
>     def data_received(self, data: bytes, datatype: asyncssh.DataType) -> None:
>         self._chan.write(data)
>
> class MySSHServer(asyncssh.SSHServer):
>     def connection_requested(self, dest_host: str, dest_port: int,
>                              orig_host: str, orig_port: int) -> \
>             asyncssh.SSHTCPSession:
>         if dest_port == 7:
>             return MySSHTCPSession()
>         else:
>             raise asyncssh.ChannelOpenError(
>                 asyncssh.OPEN_ADMINISTRATIVELY_PROHIBITED,
>                 'Only echo connections allowed')
>
> async def start_server() -> None:
>     await asyncssh.create_server(MySSHServer, '', 8022,
>                                  server_host_keys=['ssh_host_key'],
>                                  authorized_client_keys='ssh_user_ca')
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH server failed: ' + str(exc))
>
> loop.run_forever()
>
> ```

Here’s an example of this server written using the streams API. In this
case, [`connection_requested()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SSHServer.connection_requested "asyncssh.SSHServer.connection_requested")
returns a handler coroutine instead of a session object. When a new
direct TCP connection is opened, the handler coroutine is called with
AsyncSSH stream objects which can be used to perform I/O on the tunneled
connection.

> ```
> import asyncio, asyncssh, sys
>
> async def handle_connection(reader: asyncssh.SSHReader,
>                             writer: asyncssh.SSHWriter) -> None:
>     while not reader.at_eof():
>         data = await reader.read(8192)
>
>         try:
>             writer.write(data)
>         except BrokenPipeError:
>             break
>
>     writer.close()
>
> class MySSHServer(asyncssh.SSHServer):
>     def connection_requested(self, dest_host: str, dest_port: int,
>                              orig_host: str, orig_port: int) -> \
>             asyncssh.SSHSocketSessionFactory:
>         if dest_port == 7:
>             return handle_connection
>         else:
>             raise asyncssh.ChannelOpenError(
>                       asyncssh.OPEN_ADMINISTRATIVELY_PROHIBITED,
>                       'Only echo connections allowed')
>
> async def start_server() -> None:
>     await asyncssh.create_server(MySSHServer, '', 8022,
>                                  server_host_keys=['ssh_host_key'],
>                                  authorized_client_keys='ssh_user_ca')
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('SSH server failed: ' + str(exc))
>
> loop.run_forever()
>
> ```

## SFTP server [¶](https://asyncssh.readthedocs.io/en/latest/#sftp-server "Link to this heading")

The following example shows how to start an SFTP server with default
behavior:

> ```
> import asyncio, asyncssh, sys
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           sftp_factory=True)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

A subclass of [`SFTPServer`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPServer "asyncssh.SFTPServer") can be provided as the value of the SFTP
factory to override specific behavior. For example, the following code
remaps path names so that each user gets access to only their own individual
directory under `/tmp/sftp`:

> ```
> import asyncio, asyncssh, os, sys
>
> class MySFTPServer(asyncssh.SFTPServer):
>     def __init__(self, chan: asyncssh.SSHServerChannel):
>         root = '/tmp/sftp/' + chan.get_extra_info('username')
>         os.makedirs(root, exist_ok=True)
>         super().__init__(chan, chroot=root)
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           sftp_factory=MySFTPServer)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

More complex path remapping can be performed by implementing the
[`map_path`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPServer.map_path "asyncssh.SFTPServer.map_path") and
[`reverse_map_path`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPServer.reverse_map_path "asyncssh.SFTPServer.reverse_map_path") methods. Individual
SFTP actions can also be overridden as needed. See the [`SFTPServer`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPServer "asyncssh.SFTPServer")
documentation for the full list of methods to override.

## SCP server [¶](https://asyncssh.readthedocs.io/en/latest/#scp-server "Link to this heading")

The above server examples can be modified to also support SCP by simply
adding `allow_scp=True` alongside the specification of the `sftp_factory`
in the [`listen()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.listen "asyncssh.listen") call. This will use the same [`SFTPServer`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.SFTPServer "asyncssh.SFTPServer")
instance when performing file I/O for both SFTP and SCP requests. For
instance:

> ```
> import asyncio, asyncssh, sys
>
> async def start_server() -> None:
>     await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
>                           authorized_client_keys='ssh_user_ca',
>                           sftp_factory=True, allow_scp=True)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

# Reverse Direction Example [¶](https://asyncssh.readthedocs.io/en/latest/#reverse-direction-example "Link to this heading")

One of the unique capabilities of AsyncSSH is its ability to support
“reverse direction” SSH connections, using the functions
[`connect_reverse()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.connect_reverse "asyncssh.connect_reverse") and [`listen_reverse()`](https://asyncssh.readthedocs.io/en/latest/api.html#asyncssh.listen_reverse "asyncssh.listen_reverse"). This can be
helpful when implementing protocols such as “NETCONF Call Home”,
described in [**RFC 8071**](https://datatracker.ietf.org/doc/html/rfc8071.html). When using this capability, the SSH protocol
doesn’t change, but the roles at the TCP level about which side acts
as a TCP client and server are reversed, with the TCP client taking
on the role of the SSH server and the TCP server taking on the role of
the SSH client once the connection is established.

For these examples to run, the following files must be created:

> - The file `client_host_key` must exist on the client and contain an
>   SSH private key for the client to use to authenticate itself as a
>   host to the server. An SSH certificate can optionally be provided
>   in `client_host_key-cert.pub`.
>
> - The file `trusted_server_keys` must exist on the client and contain
>   a list of trusted server keys or a `cert-authority` entry with a
>   public key trusted to sign server keys if certificates are used. This
>   file should be in “authorized_keys” format.
>
> - The file `server_key` must exist on the server and contain an SSH
>   private key for the server to use to authenticate itself to the
>   client. An SSH certificate can optionally be provided in
>   `server_key-cert.pub`.
>
> - The file `trusted_client_host_keys` must exist on the server and
>   contain a list of trusted client host keys or a `@cert-authority`
>   entry with a public key trusted to sign client host keys if
>   certificates are used. This file should be in “known_hosts” format.

## Reverse Direction Client [¶](https://asyncssh.readthedocs.io/en/latest/#reverse-direction-client "Link to this heading")

The following example shows a reverse-direction SSH client which will run
arbitrary shell commands given to it by the server it connects to:

> ```
> import asyncio, asyncssh, sys
> from asyncio.subprocess import PIPE
>
> async def handle_request(process: asyncssh.SSHServerProcess) -> None:
>     """Run a command on the client, piping I/O over an SSH session"""
>
>     assert process.command is not None
>
>     local_proc = await asyncio.create_subprocess_shell(
>         process.command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
>
>     await process.redirect(stdin=local_proc.stdin, stdout=local_proc.stdout,
>                            stderr=local_proc.stderr)
>
>     process.exit(await local_proc.wait())
>     await process.wait_closed()
>
> async def run_reverse_client() -> None:
>     """Make an outbound connection and then become an SSH server on it"""
>
>     conn = await asyncssh.connect_reverse(
>         'localhost', 8022, server_host_keys=['client_host_key'],
>         authorized_client_keys='trusted_server_keys',
>         process_factory=handle_request, encoding=None)
>
>     await conn.wait_closed()
>
> try:
>     asyncio.run(run_reverse_client())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Reverse SSH connection failed: ' + str(exc))
>
> ```

## Reverse Direction Server [¶](https://asyncssh.readthedocs.io/en/latest/#reverse-direction-server "Link to this heading")

Here is the corresponding server which makes requests to run the commands:

> ```
> import asyncio, asyncssh, sys
>
> async def run_commands(conn: asyncssh.SSHClientConnection) -> None:
>     """Run a series of commands on the client which connected to us"""
>
>     commands = ('ls', 'sleep 30 && date', 'sleep 5 && cat /proc/cpuinfo')
>
>     async with conn:
>         tasks = [conn.run(cmd) for cmd in commands]
>
>         for task in asyncio.as_completed(tasks):
>             result = await task
>             print('Command:', result.command)
>             print('Return code:', result.returncode)
>             print('Stdout:')
>             print(result.stdout, end='')
>             print('Stderr:')
>             print(result.stderr, end='')
>             print(75*'-')
>
> async def start_reverse_server() -> None:
>     """Accept inbound connections and then become an SSH client on them"""
>
>     await asyncssh.listen_reverse(port=8022, client_keys=['server_key'],
>                                   known_hosts='trusted_client_host_keys',
>                                   acceptor=run_commands)
>
> loop = asyncio.new_event_loop()
>
> try:
>     loop.run_until_complete(start_reverse_server())
> except (OSError, asyncssh.Error) as exc:
>     sys.exit('Error starting server: ' + str(exc))
>
> loop.run_forever()
>
> ```

AsyncSSH

Version 2.21.0

### [Table of Contents](https://asyncssh.readthedocs.io/en/latest/#)

- [AsyncSSH: Asynchronous SSH for Python](https://asyncssh.readthedocs.io/en/latest/#)
  - [Features](https://asyncssh.readthedocs.io/en/latest/#features)
  - [License](https://asyncssh.readthedocs.io/en/latest/#license)
  - [Prerequisites](https://asyncssh.readthedocs.io/en/latest/#prerequisites)
  - [Installation](https://asyncssh.readthedocs.io/en/latest/#installation)
    - [Optional Extras](https://asyncssh.readthedocs.io/en/latest/#optional-extras)
    - [Installing the development branch](https://asyncssh.readthedocs.io/en/latest/#installing-the-development-branch)
  - [Mailing Lists](https://asyncssh.readthedocs.io/en/latest/#mailing-lists)
- [Client Examples](https://asyncssh.readthedocs.io/en/latest/#client-examples)
  - [Simple client](https://asyncssh.readthedocs.io/en/latest/#simple-client)
  - [Callback example](https://asyncssh.readthedocs.io/en/latest/#callback-example)
  - [Interactive input](https://asyncssh.readthedocs.io/en/latest/#interactive-input)
  - [I/O redirection](https://asyncssh.readthedocs.io/en/latest/#i-o-redirection)
  - [Checking exit status](https://asyncssh.readthedocs.io/en/latest/#checking-exit-status)
  - [Running multiple clients](https://asyncssh.readthedocs.io/en/latest/#running-multiple-clients)
  - [Setting environment variables](https://asyncssh.readthedocs.io/en/latest/#setting-environment-variables)
  - [Setting terminal information](https://asyncssh.readthedocs.io/en/latest/#setting-terminal-information)
  - [Port forwarding](https://asyncssh.readthedocs.io/en/latest/#port-forwarding)
  - [Direct TCP connections](https://asyncssh.readthedocs.io/en/latest/#direct-tcp-connections)
  - [Forwarded TCP connections](https://asyncssh.readthedocs.io/en/latest/#forwarded-tcp-connections)
  - [SFTP client](https://asyncssh.readthedocs.io/en/latest/#sftp-client)
  - [SCP client](https://asyncssh.readthedocs.io/en/latest/#scp-client)
- [Server Examples](https://asyncssh.readthedocs.io/en/latest/#server-examples)
  - [Simple server](https://asyncssh.readthedocs.io/en/latest/#simple-server)
  - [Simple server with input](https://asyncssh.readthedocs.io/en/latest/#simple-server-with-input)
  - [Callback example](https://asyncssh.readthedocs.io/en/latest/#id14)
  - [I/O redirection](https://asyncssh.readthedocs.io/en/latest/#id15)
  - [Serving multiple clients](https://asyncssh.readthedocs.io/en/latest/#serving-multiple-clients)
  - [Line editing](https://asyncssh.readthedocs.io/en/latest/#line-editing)
  - [Getting environment variables](https://asyncssh.readthedocs.io/en/latest/#getting-environment-variables)
  - [Getting terminal information](https://asyncssh.readthedocs.io/en/latest/#getting-terminal-information)
  - [Port forwarding](https://asyncssh.readthedocs.io/en/latest/#id16)
  - [Direct TCP connections](https://asyncssh.readthedocs.io/en/latest/#id17)
  - [SFTP server](https://asyncssh.readthedocs.io/en/latest/#sftp-server)
  - [SCP server](https://asyncssh.readthedocs.io/en/latest/#scp-server)
- [Reverse Direction Example](https://asyncssh.readthedocs.io/en/latest/#reverse-direction-example)
  - [Reverse Direction Client](https://asyncssh.readthedocs.io/en/latest/#reverse-direction-client)
  - [Reverse Direction Server](https://asyncssh.readthedocs.io/en/latest/#reverse-direction-server)

### [Change Log](https://asyncssh.readthedocs.io/en/latest/changes.html)

### [Contributing](https://asyncssh.readthedocs.io/en/latest/contributing.html)

### [API Documentation](https://asyncssh.readthedocs.io/en/latest/api.html)

### [Source on PyPI](https://pypi.python.org/pypi/asyncssh/)

### [Source on GitHub](https://github.com/ronf/asyncssh)

### [Issue Tracker](https://github.com/ronf/asyncssh/issues)

### [Search](https://asyncssh.readthedocs.io/en/latest/search.html)
