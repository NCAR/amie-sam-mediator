## AMIE-SAM Mediator

The AMIE-SAM Mediator is a tool for mediating interactions between AMIE and
SAM (Systems Accounting Manager) at NCAR.

The AMIE server is polled regularly for "packets" that describe account
management operations. These packets are designed to be site-agnostic, and
all site-specific actions are meant to be handled by a local "service provider".
The services at NCAR are provided by SAM (and PeopleSearch). The
amie-sam-mediator package mediates between AMIE and SAM.

This repo is associated with the Docker image `ncar/amie-sam-mediator`, which
is based on the Docker image `ncar/amiemediator`; the former contains all
code and configuration specific to SAM and NCAR, while the latter contains
generic mediation code that can be used by any site.

The `ncar/amie-sam-mediator` image also uses the `ncar/sweet` image.

Refer to the following documentation for information on the base images:

- [`NCAR/sweet`](https://github.com/NCAR/sweet/wiki)
- [`NCAR/amiemediator`](https://github.com/NCAR/amiemediator/wiki)
- [`XSEDE/amieclient`](https://github.com/XSEDE/amieclient/README.md)

