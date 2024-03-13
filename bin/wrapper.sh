#!/bin/sh
#
# Wrapper for running amiemediator programs with a specific environment
#
SCRIPTDIR=`cd \`dirname $0\`; /bin/pwd`
PROGPATH=$0
PROG=`basename ${PROGPATH}`

if [ -f "${SCRIPTDIR}/${PROG}.rc" ] ; then
    . "${SCRIPTDIR}/${PROG}.rc"
fi

base_candidates="
  .
  ..
  ${SCRIPTDIR}/..
  ${SCRIPTDIR}/..
  ${SCRIPTDIR}/../..
  ${PACKAGE_DIR}
"

BASE_DIR=
for base_candidate in ${base_candidates} ; do
    if [ -d "${base_candidate}" ] && [ -f "${base_candidate}/Dockerfile" ]
    then
        BASE_DIR=`cd "${base_candidate}" ; /bin/pwd`
        break
    fi
done
if [ ":${BASE_DIR}" = ":" ] ; then
    echo "${PROG}: cannot determine package base directory" >&2
    exit 1
fi 

if [ ":${RUN_ENV}" != ":" ] && [ -d "${BASE_DIR}/${RUN_ENV}" ] ; then
    conf_candidates="${BASE_DIR}/${RUN_ENV}/config.ini"
else
    conf_candidates=""
fi

conf_candidates="${conf_candidates}
  ./config.init
  ./config.ini
  ${SCRIPTDIR}/config.init
  ${SCRIPTDIR}/config.ini
"
CONFIG_FILE=
for conf_candidate in ${conf_candidates} ; do
    if [ -f "${conf_candidate}" ] ; then
        configdir=`cd \`dirname ${conf_candidate}\` ; /bin/pwd`
        configbase=`basename ${conf_candidate}`
        CONFIG_FILE="${configdir}/${configbase}"
        break
    fi
done
if [ ":${CONFIG_FILE}" = ":" ] ; then
    echo "${PROG}: cannot determine configuration file" >&2
    exit 1
fi 

pydir_candidates="
  ${BASE_DIR}/../amiemedaator/bin
  ${SCRIPTDIR}/../../bin
  ${SCRIPTDIR}/../../amiemediator/bin
"

PYPROG=
for pydir_candidate in ${pydir_candidates} ; do
    if [ -d "${pydir_candidate}" ] && [ -f "${pydir_candidate}/${PROG}" ] && \
       [ -x "${pydir_candidate}/${PROG}" ] ; then
        pydir=`cd ${pydir_candidate} ; /bin/pwd`
        if [ ":${pydir}" = ":${SCRIPTDIR}" ] ; then
            continue
        fi
        PYPROG="${pydir}/${PROG}"
        break
    fi
done
if [ ":${PYPROG}" = ":" ] ; then
    echo "${PROG}: cannot find amiemediator/bin/${PROG} file" >&2
    exit 1
fi

CMD="${PYPROG} --configfile=${CONFIG_FILE} $@"
exec ${CMD}
exit 255
