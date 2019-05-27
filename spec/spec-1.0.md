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
      - uwsgi
    ports:
      - "80"

  db:
    image: postgres:9.4
    volumes:
      - db-data:/var/lib/postgresql/data

  uwsgi:
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

## Instance

As shown above, an instance currently must be instantiated from a container built 
from a Singularity recipe in a named folder alongside the singularity-compose.yml.
We do this for reproducibility, and because there are very few containers out
in the wild with start scripts that we could quickly pull. If this changes,
we will provide support for defining a container URI without a build context.
Here again is an example instance specification, and the fields are discussed
below:

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

### Fields

|Name| Description |
|----|-------------|
|name|The name of the instance will be "nginx" unless the user provides a "name"
field (not defined above).|
|build| a section to define how and where to build the base container from.|
|build.context| the folder with the Singularity file (and other relevant files). Must exist.
|build.recipe| the Singularity recipe in the build context folder. It defaults to `Singularity`|
|volumes| one or more files or files to bind to the instance when it's started.|
|volumes_from| shared volumes that are defined for other instances|
|ports| currently not sure how I'm going to handle this!|
