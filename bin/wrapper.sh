#!/bin/sh
WRAPPERNAME="wrapper.sh"
PROG=`basename $0`
if [ ":${PROG}" = ":${WRAPPERNAME}" ] ; then
    cat <<EOF
wrapper.sh: A wrapper script for running amiemediator programs in a custom
            environment
Usage: <link_to_wrapper.sh> <amie_prog_args>

Amiemediator programs ("amie", "test-scenario", "viewpackets") require a
site-specific configuration file and externally-defined code to be at all
useful. This script allows you to easily provide a configuration file and other
information tailored to your site.

This script is not meant to be run as "${WRAPPERNAME}". Instead, it is meant to
be linked to another file with a name matching that of an amiemediator program
and run using that name. For example, the main amiemediator program in called
"amie". To use ${WRAPPERNAME} as a wrapper for "amie", set up a directory for
your custom environment, copy ${WRAPPERNAME} to that directory, and create a
link to ${WRAPPERNAME} called "amie". For example, if your site-specific files
are all under directory "mysite", you could do this:

    \$ mkdir -p mysite/bin
    \$ cp ${WRAPPERNAME} mysite/bin
    \$ chmod +x mysite/bin/${WRAPPERNAME}
    \$ cd mysite/bin
    \$ ln -s ${WRAPPERNAME} amie

In addition to creating a link to your target program, you will want to
create a file in the same directory called "<name>.rc", where <name> is the
name of the target program (e.g. "amie.rc"). ${WRAPPERNAME} will source this
file before doing anything else.

There are four environment variables that ${WRAPPERNAME} will subsequently use
if they are set and not empty: CONFIG_INI, PACKAGE_DIR, RUN_ENV, and
AMIEMEDIATOR_DIR.

CONFIG_INI is assumed to name a configuration file. PACKAGE_DIR is assumed to
name a directory containing all of your site-specific files. (In the example
above, it would be "mydir".) RUN_ENV is assumed to name a subdirector under
${PACKAGE_DIR} containing run-time configuration files; it is typically
something like "test", "prod", or "dev", for example. AMIEMEDIATOR_DIR is the
top-level directory where the amiemediator package is installed.

If CONFIG_INI is not set or does not name a readable file, ${WRAPPERNAME} will
look for it under \$PACKAGE_DIR/\$RUN_ENV.

If PACKAGE_DIR is not set, ${WRAPPERNAME} will search for a reasonable
default: it will look in the parent directory of the ${WRAPPERNAME} script,
the grandparent directory of the script, the script directory, the current
directory, the parent of the current directory, in order. Specifically, it
will look for a "config.init" or "config.ini" file in each of these directories
and in the \$RUN_ENV subdirectory of these directories.

If AMIEMEDIATOR_DIR is not set, ${WRAPPERNAME} will search
\$PACKAGE_DIR/../amiemediator and \$PACKAGE_DIR/../../amiemediator.

All amiemediator programs ("amie", "viewpackets", etc.) support environment
variables CONFIG_INI, USAGE, LOCALSITE_INTRO_TEXT, INTRO_TEXT,
LOCALSITE_CONFIG_TEXT, and LOCAL_SITE_ENV_TEXT. CONFIG_INI identifies the
configuration file, while the other variables are used by the "--help"
command-line option if they are set.

EOF
    echo $PROG
    exit 0
fi

SCRIPTDIR=`cd \`dirname $0\`; /bin/pwd`

if [ -f "${SCRIPTDIR}/${PROG}.rc" ] ; then
    . "${SCRIPTDIR}/${PROG}.rc"
fi

conf_base_candidates="config.init config.ini"
run_env_candidates=". ${RUN_ENV}"

pkg_dir_candidates="
  ${PACKAGE_DIR}
  ${SCRIPTDIR}/..
  ${SCRIPTDIR}/../..
  ${SCRIPTDIR}
  .
  ..
"

if [ ":${CONFIG_INI}" != ":" ] ; then
    if [ ! -f "${CONFIG_INI}" ] || [ ! -r "${CONFIG_INI}" ] ; then
        echo "$PROG: \$CONFIG_INI file is not readable" >&2
        exit 1
    fi
    config_dir=`dirname ${CONFIG_INI}`
fi

CONFIG_FILE=
ENV_DIR=
PKG_DIR=
for pkg_dir_candidate in ${pkg_dir_candidates} ; do
    for run_env_candidate in ${run_env_candidates} ; do
        for conf_base_candidate in ${conf_base_candidates} ; do
            p="${pkg_dir_candidate}/${run_env_candidate}/${conf_base_candidate}"
            if [ -f "${p}" ] && [ -r "${p}" ] ; then
                CONFIG_FILE="${p}"
                ENV_DIR="${run_env_candidate}"
                PKG_DIR="${pkg_dir_candidate}"
                break
            fi
        done
        if [ ":${PKG_DIR}" != ":" ] ; then
            break
        fi
    done                
    if [ ":${PKG_DIR}" != ":" ] ; then
        break
    fi
done
if [ ":${CONFIG_INI}" = ":" ] ; then
    CONFIG_INI="${CONFIG_FILE}"
fi
export CONFIG_INI

if [ ":${PKG_DIR}" != ":" ] ; then
    PKG_DIR=`cd ${PKG_DIR} ; /bin/pwd`
else
    PKG_DIR=`/bin/pwd`
fi

amie_file=src/mediator.py

amie_dir_candidates="${AMIEMEDIATOR_DIR}
${PKG_DIR}/../amiemediator
${PKG_DIR}/../../amiemediator
"
AMIE_DIR=
for amie_dir_candidate in ${amie_dir_candidates} ; do
    check_file=${amie_dir_candidate}/${amie_file}
    if [ -f ${check_file} ] ; then
        AMIE_DIR="${amie_dir_candidate}"
        break
    fi
done
if [ ":${AMIE_DIR}" = ":" ] ; then
    echo "${PROG}: cannot determine amiemediator package base directory" >&2
    exit 1
fi
AMIEMEDIATOR_DIR=`cd ${AMIE_DIR} ; /bin/pwd`
export AMIEMEDIATOR_DIR

PYPROG="${AMIEMEDIATOR_DIR}/bin/${PROG}"
if [ ! -f ${PYPROG} ] || [ ! -x ${PYPROG} ] ; then
    echo "${PROG}: ${PYPROG} does not exist or is not executable" >&2
    exit 1
fi
export PYPROG

CMD="${PYPROG} $@"
exec ${CMD}
exit 255
