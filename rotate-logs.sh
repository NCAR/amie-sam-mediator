#!/bin/sh#!/bin/sh
PROG=rotate-logs.sh
DESC="Rotate logs by attaching month-tagged links"
USAGE1="$PROG logdir"
USAGE2="$PROG -h|--help"
HELP_TEXT="
        Given a log directory name, make sure every file in the directory with
        a name ending in '.log' and starting with a non-digit has a
        corresponding link with a name that begins with the month in 'YYYY-mm-'
        format and ends in the target file name.
        failed requests are found.
        
        The following options are supported:

          -h|--help
             Print help text and quit.
"

LOG_DIR=

while [ $# != 0 ] ; do
    arg="$1"
    shift
    case $arg in
        -h|--help)
            cat <<EOF
NAME
        $PROG - $DESC

SYNOPSIS
        $USAGE1
        $USAGE2

DESCRIPTION$HELP_TEXT
EOF
            exit 0 ;;
        -*)
            echo "$PROG: invalid option: $arg" >&2
            exit 2 ;;
        *)
            LOG_DIR="$arg" ;;
    esac
done
if [ ":${LOG_DIR}" = ":" ] ; then
    echo "$PROG: log directory argument is required" >&2
    exit 1
fi
if [ ! -d "${LOG_DIR}" ] ; then
    echo "$PROG: '${LOG_DIR}' is not a directory" >&2
    exit 1
fi

MONTH=`date +%Y-%m`
cd ${LOG_DIR} || exit 1
for log in [a-zA-Z]*.log ; do
    if [ ! -f "${log}" ] ; then
        continue
    fi
    set : `ls -l ${log}`
    nlinks=$3
    if [ $nlinks = 1 ] ; then
        exmonth=`sed -n -e 's/^\(2[0-9][0-9][0-9]-[01][0-9]\)-[0-3][0-9] .*/\1/p' "${log}" | head -1`
        exmonth_log="${exmonth}-${log}"
        ln "${log}" "${exmonth_log}"
    fi
    month_log="${MONTH}-${log}"
    if [ ! -f ${month_log} ] ; then
        rm -f "${log}" || exit 1
        touch "${month_log}" || exit 1
        ln "${month_log}" "${log}" || exit 1
    fi
done

exit 0


