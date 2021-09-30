# Singularity Compose Version 2.0

The second version of the singularity compose spec has added options for
starting an instance, starting, exec'ing and running commands after that. Note that spec v2.0 is
supported for Singularity Compose versions 0.1.0 and later.

## Overview

Here is a simple example of a 2.0 spec. The full example is provided at
[singularity-compose-examples](https://github.com/singularityhub/singularity-compose-examples/tree/master/v2.0/ping).

```yaml
version: "2.0"
instances:
  alp1:
    build:
      context: ./
      options:
        - fakeroot
    ports:
      - "1025:1025"
    start:
      options:
        - fakeroot
    exec:
      options: 
        - "env-file=myvars.env"
      command: printenv SUPERHERO
  alp2:
    build:
      context: ./
      options:
        - fakeroot
    ports:
      - "1026:1026"
    start:
      options:
        - fakeroot
    depends_on:
      - alp1
```

You'll notice that this differs from v1.0 because we've added groups for start, exec,
and run options. Start options and arguments are provided to the instance at start,
while exec options and arguments are exec'd to the instance after creation (only
if an exec argument exists). In the example above, we want to generate
two instances, each with an alpine base, and use fakeroot so that sudo is not required.


## Networking

Singularity Compose 0.1.0 later (version 2.0 of the spec here) supports using
fakeroot for start arguments, as shown above. However, you likely will need to
add the user of interest as follows:

```bash
$ sudo singularity config fakeroot --add $USER
```

The above command would add _your_ username. You'll also need to update the fakeroot
network configuration at `/usr/local/etc/singularity/network/40_fakeroot.conflist`
(or replace with the prefix where you installed Singularity):

```json
{
    "cniVersion": "0.4.0",
    "name": "fakeroot",
    "plugins": [
        {
            "type": "bridge",
            "bridge": "sbr0",
            "isGateway": true,
            "ipMasq": true,
            "ipam": {
                "type": "host-local",
                "subnet": "10.22.0.0/16",
                "routes": [
                    { "dst": "0.0.0.0/0" }
                ]
            }
        },
        {
            "type": "firewall"
        },
        {
            "type": "portmap",
            "capabilities": {"portMappings": true},
            "snat": true
        }
    ]
}
``` 

If you don't want to make these changes, then you won't be able to use fakeroot
as a network (start) option (you might still be able to use it as a build option).

## Network Group

By default `singularity-compose` will allocate an IP address for every instance in 
the listed yaml file. Binding an IP address to a process requires `sudo` so in certain
scenarios in which access to a privileged user isn't an option, you might want to tell
`singularity-compose` not to allocate an IP address, that way you can run instances 
without `sudo`. 

The example below will run a container that exposes the port `5432` to the host. 

```yaml
  instance1:
    ...
    network:
      allocate_ip: true | false
    ports:
      - 5432:5432
```

**Obs.:** In recent versions of the Singularity CLI, there is the need for tweaking the 
`/etc/singularity/singularity.conf` to allow `fakeroot` to bind to ports otherwise 
an error will be thrown at container execution similar to this:

```
INFO:    Converting SIF file to temporary sandbox...
ERROR:   Network fakeroot is not permitted for unprivileged users.
INFO:    Cleaning up image...
```

To allow fakeroot to bind ports without sudo you need to execute this:

```
echo "allow net networks = bridge, fakeroot" >> /etc/singularity/singularity.conf
```

## Start Group

Startscript options generally include those for networking, and any other flags
that you want to provide. The previous "command" option is deprecated, and moved to be under the "start"
group as "args," since we are technically providing arguments to the start script. 
As an example in the configuration above, we are starting with options
for `--fakeroot`:

```yaml
  alp1:
    ...
    start:
      options:
        - fakeroot
```

You could also add "args" here within the start group to provide arguments to the start script.


## Environment

While Singularity compose doesn't currently have support for an environment 
section, it's easy to add custom environments by way of binding an environment
file to the instance! For example:

```yaml
    build:
      context: ./app
    volumes:
      - ./env_file.sh:/.singularity.d/env/env_file.sh
```

Any file that is found in the `.singularity.d/env` folder will be sourced.
For example, you could define or export variables like so:

```bash
#!/bin/bash
MYNAME=dinosaur
export MYNAME
```

Make sure to export variables.


## Exec Group

The exec group, if defined, will run an exec command after an instance is started.
There must be a command defined for this to run. For example,
if you want to provide a one off environment variable to an exec (run after start)
then you can do the following:

```yaml
    exec:
      options: 
        - "env-file=myvars.env"
      command: printenv MYNAME
```

As with the above, make sure to export variables.
We are only printing there to show that it works.

## Run Group

Let's say that you want to start the container, exec a command, and then run the container.
This is possible with the run group, and your container must define a runscript.
If you just want the run to happen (without options or arguments) you can do:

```yaml
  alp1:
    run: []
```

And if you want args or options, you can again add them:

```yaml
  alp1:
    run:
      args: "arg1 arg2 arg3"
      options: 
        - "env-file=myvars.env"
```

The run and exec sections are separate to allow you to run both, or either without
the other.

## Instance

An instance currently must be instantiated from a container built 
from a Singularity recipe in a named folder (the example above) 
alongside the singularity-compose.yml:

```
  nginx:
    build:
      context: ./nginx
      recipe: Singularity.nginx
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./uwsgi_params.par:/etc/nginx/uwsgi_params.par:ro
    volumes_from:
      - uwsgi
    ports:
      - "80"
```

or from a container unique resource identifier (uri) that can be pulled
to a local directory with the same name as the section.

```
  nginx:
    image: docker://vanessa/sregistry_nginx
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./uwsgi_params.par:/etc/nginx/uwsgi_params.par:ro
    volumes_from:
      - uwsgi
    ports:
      - "80"
```

We build or pull a local container for reproducibility. The first approach,
building from a local file, is recommended as you have full control over
the environment and startscript, and there are likely few containers out in the
wild (and ready to be pulled) that have the correct entry and start scripts
for your application. In the case that you *do* want to pull
a container (and use the existing startscript or entrypoint) you can do that
as follows:

```
  nginx:
    image: docker://vanessa/sregistry_nginx
...
```

Customization of an image (e.g., labels, help, post) is out of
scope for singularity-compose, and you must build from a recipe instead.
The fields for instances are discussed below:


### Fields

|Name| Description |
|----|-------------|
|name|The name of the instance will be "nginx" unless the user provides a "name"
field (not defined above).|
|build| a section to define how and where to build the base container from.|
|build.context| the folder with the Singularity file (and other relevant files). Must exist.
|build.recipe| the Singularity recipe in the build context folder. It defaults to `Singularity`|
|build.options| a list of one or more options (single strings for boolean, or key value pairs for arguments) to provide to build.  This is where you could provide fakeroot.|
|start| a section to define start (networking) arguments and options |
|start.options| a list of one or more options for starting the instance |
|start.args| arguments to provide to the startscript when starting the instance |
|run| a section to define run arguments and options (container must have runscript) |
|run.options| a list of one or more options for running the instance after start |
|run.args| arguments to provide when running the instance |
|exec| a section to define an exec directly after instance start (requires a command) |
|exec.options| a list of one or more options for exec'ing to the instance |
|exec.command| the command and arguments to provide the instance exec |
|image| is looked for after a build entry. It can be a unique resource identifier, or container binary. |
|volumes| one or more files or files to bind to the instance when it's started.|
|volumes_from| shared volumes that are defined for other instances|
|ports| currently not sure how I'm going to handle this!|
|post| a section of post commands and arguments, run after instance creation |
|post.commands| a list of commands to run (directly or a script) on the host |
