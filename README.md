Router Restart
==============

This script can:
- Reconnect to the Internet
- Reboot the router


Motivation
----------

Even in 2016 you sometimes have to:
  1. Wake up from your lovely workspace...
  2. Step to that annoying router...
  3. Just to press a silly button!

Now you have a simpler approach.


Installation
------------

Supported Python versions are: 2.6, 2.7 and 3.2+.

Grab the script via:
```bash
$ wget raw.githubusercontent.com/hcpl/router-restart/master/router-restart.py
# if you want the whole repo:
$ git clone github.com/hcpl/router-restart
```

Make a symbolic link for easier interaction:
```bash
$ ln -s router-restart.py rr    # UNIX
```
or
```cmd
> mklink rr router-restart.py    :: Windows (run this code in
                                 :: an administrator console)
```


You could also need to install [`requests`][Requests site],
if you don't have one:
```bash
$ pip install requests
```
or consider upgrading it (e.g. version 2.2.1 packaged in the
Ubuntu 14.04 repo is too old):
```bash
$ pip install --upgrade requests
```
See notes[1] for details.


Usage
-----

To reconnect to the Internet:
```bash
$ rr
```

To reboot the router:
```bash
$ rr -r
# or
$ router-restart --reboot
```


Not a 192.168.0.1 IP? Use:
```bash
$ rr -h 45.192.4.33
    # The default one is 192.168.0.1
```

Pick a port other than 80:
```bash
$ rr -p 8080
    # 80 by default
```

Usually, routers require a login process. Try this:
```bash
$ rr -u router_user -w very_difficult_and_long_password
    # -u admin -w admin
```

If tired of typing single options, use a JSON-based configuration file:
```bash
$ rr -c config-file.json
```
which looks like:
```json
{
    "host": "10.35.0.1",
    "port": 8080,
    "username": "myadmin",
    "password": "router-password"
}
```
The script also automatically uses the `.router-restart.conf` in your
home directory.


Specify verbosity options by multiple 'v' letters:
```bash
$ rr -v       # Verbose
$ rr -vv      # More verbose
$ rr -vvv     # Even more verbose
$ rr -vvvv    # The most verbose
              # You can add more 'v' letters as well,
              # the result is the same as -vvvv
```

... or by a single number:
```bash
$ router-restart --verbose 2    # --verbose <num> corresponds to
                                #  -v with 'v' letters repeated <num> times
```

Dry-run checkouts:
```bash
$ rr -s
# or
$ router-restart --simulate
```


Currently supported devices
---------------------------

Help in extending this list!
- TP-Link
  - TL-WR841N
  - TL-WR941N
  - ... maybe all other TP-Link\`s?


Notes
-----

1. This script uses a tuple timeout feature in [`requests`][Requests site]
   requests, introduced by the commit
   kennethreitz/requests@c2aeaa3959b5754f5b39a45bceff91b196b6c986
   before releasing the 2.4.0 version.

[Requests site]: http://docs.python-requests.org
