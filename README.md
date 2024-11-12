# amie-sam-mediator
A tool for mediating interactions between AMIE and SAM (Systems Accounting
Manager) at NCAR.

The XSEDE/amieclient package is a python library for the AMIE REST API. It
defines all data packets and low-level messaging methods, but leaves all
higher-level and back-end processing tasks to the local service provider.

The NCAR/amiemediator package attempts to simplify the implementation of these
other tasks by providing a back-end ServiceProvider API and a configurable
daemon that handles all interactions with the central AMIE server.

The NCAR/amie-sam-mediator includes an implementation of the ServiceProvider
API that interacts with the SAM and PeopleSearch applications, and configuration
files that tie everything together.

The amie-sam-mediator package must be installed under a directory in which the
amiemediator and amieclient packages are also installed.

The mediator daemon program is amie-sam-mediator/bin/amie. It is actually just
a wrapper script that runs the amiemediator/bin/amie program after setting
up the environment with custom documentation files and python modules specific
to the SAM service provider.

Users can interact with AMIE tasks using the SAM UI; SAM versions from 1.19
include a "Tasks" interface available from the main manu bar.
    
