# Singularity Compose Version 1.0

## Overview

The main format of the file is yaml. We must define a version and one or more
instances under "instances." Here is a full example for reference.

```yaml
version: "1.0"
instances:

  nginx:
    build:
      context: ./nginx
      recipe: Singularity.nginx
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./uwsgi_params.par:/etc/nginx/uwsgi_params.par:ro
    volumes_from:
      - app
    ports:
      - "80"

  db:
    image: postgres:9.4
    volumes:
      - db-data:/var/lib/postgresql/data

  app:
    build:
      context: ./app
    volumes:
      - .:/code
      - ./static:/var/www/static
      - ./images:/var/www/images
    ports:
      - "5000:80"
    depends_on:
      - nginx
```

Each of nginx, uwsgi, and db are instances to be built as containers, and run
as instances. 

## Networking

Since Singularity does not (currently) have control over custom networking,
all instance ports are mapped to the host (localhost) and we don't have any
configuration settings to control this (how to handle ports?)

## Startscript arguments

It is possible to use the `command` option to pass arguments to an instance's
startscript.

The following example shows how to pass the arguments `arg0 arg1arg2` to the
startscript of instance `app`,

```yaml
  app:
    build:
      context: ./app
    command: "arg0 arg1 arg2"
```

## Environment

While Singularity compose doesn't currently have support for an environment 
section, it's easy to add custom environments by way of binding an environment
file to the instance! For example:

```yaml
  app:
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
|image| is looked for after a build entry. It can be a unique resource identifier, or container binary. |
|volumes| one or more files or files to bind to the instance when it's started.|
|volumes_from| shared volumes that are defined for other instances|
|ports| currently not sure how I'm going to handle this!|
|post| a section of post commands and arguments, run after instance creation |
|post.commands| a list of commands to run (directly or a script) on the host |
