---
title: 'Singularity Compose: Orchestration for Singularity Instances'
tags:
  - containers
  - singularity
  - linux
  - orchestration
authors:
 - name: Vanessa Sochat
   orcid: 0000-0002-4387-3819
   affiliation: 1
affiliations:
 - name: Stanford University Research Computing
   index: 1
date: 24 June 2019
bibliography: paper.bib
---

# Summary

Singularity Compose is an orchestration tool for Singularity container instances.

![Singularity Compose](singularity-compose.png)

The Singularity container technology started to become popular in 2016,
as it offered a more secure option to run encapsulated environments [@Kurtzer2017-xj].
Traditionally, this meant that Singularity users could run an script built into the container
(called a runscript), execute a custom command, or shell into a container. 
Unlike Docker [@Merkel2014-da], these basic interactions simply interacted with processes in the 
foreground (e.g., running a script and exiting) and were not appropriate to run 
background services. This was a task for container instances [@SingularityInstances].

A container instance [@SingularityInstances] equates to running a container in a detached or
daemon mode. Instances allow for running persistent services in the background,
and then interaction with these services from the host and other containers.
Examples of services include databases, web servers, and associated applications
that interact with them. While a container technology can provide command line
and other programmatic interfaces for interaction with instances, what is also needed
is a configuration file for orchestration and customization of several instances.
For sibling container technology Docker, Docker Compose [@DockerCompose] was developed 
for this purpose. For local and production usage, the user could create a `docker-compose.yml` 
file to define services, volumes, ports exposed, and other customizations to networking and environment
[@DockerCompose]. Notably, there was strong incentive for the development of such a tool,
because Docker Compose existed before Kubernetes was available in the middle of 2015 [@Wikipedia_contributors2019-bw].

No equivalent orchestration tool was created for Singularity container
instances. While Singularity has empowered enterprise users to run 
services via platforms such as Kubernetes [@Meyer2019-sd], these platforms come
with privilege. It is often the case that a production Kubernetes cluster is not 
readily available to a user via his or her institution, or that the user 
cannot pay a cloud provider to deploy one. However, this does not imply that
a non enterprise user (e.g., an open source developer
or academic) would not benefit from such an orchestration tool. Unfortunately,
since the current trend and strongest potential for making profits is centered
around encouraging usage of enterprise tools like Kubernetes [@Wikipedia_contributors2019-bw],
there is not any urgent incentive on part of the provider companies to 
invest in a non-enterprise orchestration tool. It is logical, rational, and
understandable that companies exist to make profit, and must make profit
to exist. As the need is unfulfilled, it is the responsibility of the open source community to step up.


## Singularity Compose

The solution for orchestration of container instances from the open source
community is Singularity Compose [@SingularityCompose]. Singularity Compose 
is software for non enterprise users to easily create a configuration file to 
control creation and interaction of Singularity container instances.
It allows for the creation of a `singularity-compose.yml` file, in which
the user can define one or more container services, optionally with exposed ports
and volumes on the host. The user can easily define a container binary
to build or pull from a remote resource, along with custom scripts to
run after creation of the instances. Singularity Compose handles designation
of addresses on a local bridge network for each container, and creation of
resource files to bind to the containers to "see" one another. 
Importantly, by way of adding a Singularity Compose to a repository,
a user is ensuring not just reproducibility of a container recipe, but also
reproducibility of it's build and creation of services. For example, a simplified
version of a sequence of steps to build two containers and bring them up
as instances might look like this:

```bash
$ sudo singularity build app/app.sif app/Singularity
$ sudo singularity build nginx/nginx.sif nginx/Singularity.nginx

$ singularity instance start \
   --bind nginx.conf:/etc/nginx/conf.d/default.conf \
   --bind nginx/uwsgi_params.par:/etc/nginx/uwsgi_params.par \
   --bind nginx/cache:/var/cache/nginx \
   --bind nginx/run:/var/run \
   --bind app:/code \
   --bind static:/var/www/static \
   --bind images:/var/www/images \
   --bind etc.hosts:/etc/hosts \
   --net --network-args "portmap=80:80/tcp" --network-args "IP=10.22.0.2" \
   --hostname nginx --writable-tmpfs nginx/nginx.sif nginx

$ singularity instance start \
   --bind app:/code \
   --bind static:/var/www/static \
   --bind images:/var/www/images \
   --bind etc.hosts:/etc/hosts \
   --net --network-args "portmap=8000:8000/tcp" --network-args "IP=10.22.0.3" \
   --hostname app --writable-tmpfs app/app.sif app

$ singularity instance list
```

This is a complicated set of commands. In the above commands, we
first build the two containers. There are no checks here if the recipes
exist, or if the containers themselves already exist.
We then start instances for them. If we save these commands in a file,
we need to consistently hard code the paths to the container binaries,
along with the ip addresses, hostnames, and volumes. There are no checks
done before attempting the creation if the volumes meant to be bound
actually exist. We also take for granted that we've already generated an 
`etc.hosts` file to bind to the container at `/etc/hosts`, which will
define the container instances to have the same names supplied with `--hostname`
so that instances can "see" one another. For the networking, we have
to be mindful of the default bridge provided by Singularity, along with how
to specify networking arguments under different conditions. This entire practice
is clearly tedious. For a user to constantly need to generate and then
re-issue these commands, it's not a comfortable workflow. However, 
with Singularity Compose, the user writes a `singularity-compose.yml`
file once:

```yaml
version: "1.0"
instances:

  nginx:
    build:
      context: ./nginx
      recipe: Singularity.nginx
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./uwsgi_params.par:/etc/nginx/uwsgi_params.par
      - ./nginx/cache:/var/cache/nginx
      - ./nginx/run:/var/run
    ports:
      - 80:80
    depends_on:
      - app
    volumes_from:
      - app

  app:
    build:
      context: ./app
    volumes:
      - ./app:/code
      - ./static:/var/www/static
      - ./images:/var/www/images
    ports:
      - 8000:8000
```

And then can much more readily see and reproduce generation of the same services.
The user can easily build all non-existing containers, and bring up all services
with one command:

```bash
$ singularity-compose up
```

And then easily bring services down, restart, shell into a container, execute
a command to a container, or run a container's internal runscript.

```bash
$ singularity-compose down                   # stop services
$ singularity-compose restart                # stop and start services
$ singularity-compose shell app              # shell into an instance
$ singularity-compose exec app "Hello!"      # execute a command
$ singularity-compose run app                # run internal runscript
```

These interactions greatly improve both reproducibility and running of
any development workflow that is not appropriate for an enterprise cluster but
relies on orchestration of container instances.

For the interested reader, the complete documentation for Singularity Compose [@SingularityCompose]
is provided, along with the code on GitHub [@SingularityComposeGithub]. For 
additional walkthroughs and complete examples, we direct the reader to the examples 
repository, also on GitHub [@SingularityComposeExamples]. Contribution by way
of additional examples, questions, or requests for development of a new example
are appreciated and welcome.


# References
