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

## [0.0.x](https://github.com/singularityhub/singularity-compose/tree/master) (0.0.x)
 - version 2.0 of the spec with added network and exec options (0.1.0)
   - stop option added (equivalent functionality to down)   
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
