# CHANGELOG

This is a manually generated log to track changes to the repository for each release.
Each section should include general headers such as **Implemented enhancements**
and **Merged pull requests**. Critical items to know are:

 - renamed commands
 - deprecated / removed commands
 - changed defaults
 - backward incompatible changes
 - migration guidance
 - changed behaviour

The versions coincide with releases on pypi.

## [0.1.x](https://github.com/singularityhub/singularity-compose/tree/master) (0.1.x)
 - improve linting and docs on jsonschma (checks install) (0.1.18)
 - add support for instance replicas (0.1.17)
 - fix check command validation (0.1.16)
 - fix a bug triggered when using startoptions in conjunction with network=false (0.1.15)
 - bind volumes can handle tilde expansion (0.1.14)
 - fix module import used by check command (0.1.13)
 - adding jsonschema validation and check command (0.1.12)
   - implement configuration override feature
   - implement `--preview` argument for the `check` command
 - add network->enable option on composer file (0.1.11)
 - add network->allocate_ip option on composer file (0.1.10)
 - version 2.0 of the spec with added fakeroot network, start, exec, and run options (0.1.0)
   - stop option added (equivalent functionality to down)
   - spython version 0.1.0 with Singularity 3.x or greater required

## [0.0.x](https://github.com/singularityhub/singularity-compose/tree/master) (0.0.x)
 - removed check for sudo when adding network flags (0.0.21)
 - singularity-compose down supporting timeout (0.0.20)
 - command, ability to associate arguments to the instance's startscript (0.0.19)
 - depends\_on, check circular dependencies at startup and shutdown in reverse order (0.0.18)
 - resolv.conf, etc.hosts generated if needed, network disabled non-sudo users (0.0.17)
 - resolv.conf needs to bind by default (0.0.16)
 - adding run command (0.0.15)
 - ensuring that builds are streamed (0.0.14)
 - adding more build options to build as build-flags (0.0.13)
 - when not using sudo, need to set --network=none, and catching exec error (0.0.12)
 - pyaml version should be for newer kind, and still check for attribute (0.0.11)
 - alpha release with simple (single container) working example (0.0.1)
 - dummy release (0.0.0)
