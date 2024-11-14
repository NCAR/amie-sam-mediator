## Environment and Entrypoint Processing

The amie-sam-mediator package is set up to use docker-compose. By convention,
there are separate docker-compose configurations for development, test, and
production environments; these are in the `dev`, `test`, and `prod`
subdirectories, respectively.

Within each of these subdirectories, there is a `.env` file and a
`docker-compose.yml` file. The `.env` file contains definitions of environment
variables used by docker-compose. These are generally passed into the
containers as well. Refer to the contents of these files for details.
These directories should also contain `config.ini` files, which are the
application configuration files for the `amie` program.

Included among the environment variable defined in `.env` files are
`LOCAL_SECRETS`, `LOCAL_CONFIG`, `LOCAL_DATA`, `SECRETS_VOL`, `CONFIG_VOL`,
and `DATA_VOL`. The first three are names of local host directories that will
be mounted in the containers using the container mount points identified
by the second three.

The default entrypoint for the `amie-sam-mediator` image is the script
`sbin/entrypoint.sh` from the SWEET image. This entrypoint will scan the
`$SECRETS_VOL` and `$CONFIG_VOL` directories and copy secret/configuration
files into the container directories identified by variables `SECRETS_DIR` and
`CONFIG_DIR`, respectively, using the SWEET `flatten-config-tree` script;
this script uses the `PACKAGE`, `SERVICE`, `RUN_ENV` environment variables
to select which files under `$SECRETS_VOL` and `$CONFIG_VOL` to copy.
Specifically, it will copy files from the following subdirectories:

  .              
  ./\$RUN_ENV/
  ./\$PACKAGE/
  ./\$PACKAGE/\$RUN_ENV/
  ./\$PACKAGE/\$SERVICE
  ./\$PACKAGE/\$SERVICE/\$RUN_ENV

The `RUN_ENV` variable should be set in the `.env` files, `SERVICE` should be
set in the `docker-compose.yml` files, and `PACKAGE` will be defined in the
`amie-sam-mediator` image itself.


