#!/bin/sh
PROG=opsmonitor.sh
DESC="Monitor/restart containers, email alerts"
USAGE1="$PROG [-c|--context=compose-dir] [-e|--email=addr]
                      [-l|--logdir=logdir]"
USAGE2="$PROG -h|--help"
HELP_TEXT="
        Given a docker-compose context directory for a amie-sam-mediator
        deployment, verify that all containers are up; restart the containers
        as necessary. Email a report to the indicated address if anything
        interesting happens. Also rotate logs.
        
        The following options are supported:

          -c|--context=compose-dir
             A docker-compose context directory.

          -e|--email=email_addr
             The email address that alert emails will be sent to.

          -l|--logdir=logdir
             The directory containing application logs.

          -h|--help
             Print help text and quit.
"
ENVIRONMENT_TEXT="
        CONTEXT_DIR
            The default docker-compose context directory.

        EMAIL_ADDR
            The default alert email address.

        LOG_DIR
            The default log directory.

        DEBUG_OPS_MONITOR
            If set and not empty, standard output and standard error will not be
            redirected to a log file, and no report will be sent.
"
SCRIPTDIR=`cd \`dirname $0\`; /bin/pwd`
ROTATE_LOGS="${SCRIPTDIR}/rotate_logs.sh"

RC_OK=0
RC_WARN=1
RC_ERR=2
RC_SIG=3

MAILER=${MAILER:-mailx}
TMPDIR="/tmp/amie-opmonitor$$.d"
LOG=${TMPDIR}/log
REPORT=${TMPDIR}/report
RUNLOG="${HOME}/amie-opsmonitor.log"
MONTH=`date +%Y-%m`
RUNLOG_LINK="${MONTH}-${RUNLOG}"

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
        -c?*)
            CONTEXT_DIR=`expr "${arg}" : '-c\(.*\)'` ;;
        --context=*)
            CONTEXT_DIR=`expr "${arg}" : '--context=\(.*\)'` ;;
        -c|--context)
            CONTEXT_DIR="$1"
            shift ;;
        -e?*)
            EMAIL_ADDR=`expr "${arg}" : '-e\(.*\)'` ;;
        --email=*)
            EMAIL_ADDR=`expr "${arg}" : '--email=\(.*\)'` ;;
        -e|--email)
            EMAIL_ADDR="$1"
            shift ;;
        -l?*)
            LOG_DIR=`expr "${arg}" : '-l\(.*\)'` ;;
        --logdir=*)
            LOG_DIR=`expr "${arg}" : '--logdir=\(.*\)'` ;;
        -l|--logdir)
            LOG_DIR="$1"
            shift ;;
        -*)
            echo "$PROG: invalid option: $arg" >&2
            exit 2 ;;
    esac
done

export CONTEXT_DIR EMAIL_ADDR
exec 3>&1
exec 4>&2

main() {
    validate_cmdline

    cd ${CONTEXT_DIR} || exit 1
    CONTEXT_DIR=`pwd`
    
    setup_tmpdir

    new_month=n
    if [ ! -f "${RUNLOG_LINK}" ] ; then
        new_month=y
        rm -rf ${RUNLOG}
        :> ${RUNLOG_LINK}
        ln ${RUNLOG_LINK} ${RUNLOG}
    fi
    log "$PROG Starting" >>${RUNLOG}

    log_redirect

    if [ $new_month = y ] ; then
        bounce # force log rotation
        rc=$?
    fi
    
    check_status
    RC=$?
    if [ $rc = ${RC_ERR} ] ; then
        RC=$rc
    fi

    log_unredirect
    
    if [ ${RC} != 0 ] ; then
        send_report $RC
    fi
    
    cleanup

    log "$PROG Complete" >>${RUNLOG}
    return ${rc}
}

validate_cmdline() {
    check_cmd=:
    if [ ":${CONTEXT_DIR}" = ":" ] ; then
        echo "$PROG: -c|--context argument is required" >&2
        check_cmd="exit 1"
    fi
    if [ ":${EMAIL_ADDR}" = ":" ] ; then
        echo "$PROG: -e|--email argument is required" >&2
        check_cmd="exit 1"
    fi
    eval $check_cmd
}

setup_tmpdir() {
    trap "cat ${LOG} >>${RUNLOG} ; rm -rf $TMPDIR ; exit ${RC_SIG}" 0 1 2 13 15
    mkdir -p ${TMPDIR} || exit 1
    rm -rf ${TMPDIR}/*
}

cleanup() {
    cat ${LOG} >>${RUNLOG}
    trap "" 0
    rm -rf $TMPDIR
}

log_redirect() {
    if [ ":${DEBUG_OPS_MONITOR}" = ":" ] ; then
        exec >${LOG} 2>&1
    else
        :>${LOG} # so trap does not complain
    fi
}

log_unredirect() {
    if [ ":${DEBUG_OPS_MONITOR}" = ":" ] ; then
        exec >&3 2>&4
    fi
}

log() {
    tstamp=`date +%Y-%m-%dT%H:%M:%S`
    echo "${tstamp} $@"
}

check_status() {
    RC=${RC_OK}
    
    get_compose_info
    . ${TMPDIR}/compose_info

    if [ ":${OM_ADMIN_NAME}" = ":" ] ; then
        log "Note: No admin container exists - stopping and starting"
        RC=${RC_WARN}
        bounce
        if [ $? = $RC_ERR ] ; then
            RC=${RC_ERR}
        fi
    elif [ ":${OM_AMIE_NAME}" = ":" ] ; then
        log "Note: No amie container exists - restarting"
        RC=${RC_WARN}
        kick
        if [ $? = $RC_ERR ] ; then
            RC=${RC_ERR}
        fi
    fi

    get_compose_info
    . ${TMPDIR}/compose_info

    if [ ":${OM_ADMIN_NAME}" = ":" ] ; then
        log "Error: No admin container exists after (re)start"
        RC=${RC_ERR}
        return ${RC}
    elif [ ":${OM_ADMIN_NAME}" = ":" ] ; then
        log "Error: No admin container exists after (re)bounce"
        RC=${RC_ERR}
        return ${RC}
    fi
    
    check_container_status
    rc=$?
    if [ $rc != 0 ] && [ ${RC} = ${RC_OK} ] ; then
        RC=${RC_WARN}
    fi

    for attempt in 1 2 3 ; do
        if [ ${RC} != ${RC_OK} ] ; then
            log "Bounce attempt #${attempt}"
            bounce
            rc=$?

            if [ $rc != 0 ] ; then
                RC=${RC_ERR}
            else
                RC="${RC_WARN}"
            fi

            sleep 30

            get_compose_info

            check_container_status
            rc=$?
            if [ $rc != 0 ] ; then
                RC=${RC_ERR}
            fi
        fi
    done

    return ${RC}
}

get_compose_info() {
    echo "OM_COMP_NAMES=" >${TMPDIR}/compose_info
    echo "OM_ADMIN_NAME=" >>${TMPDIR}/compose_info
    echo "OM_AMIE_NAME=" >>${TMPDIR}/compose_info
    docker-compose ps --quiet | while read id ; do
        # Some versions (?) of podman-compose include the podman commands
        # being run and an exit code even when --quiet is included, which is
        # stupid and annoying and something we need to deal with
        case ${id} in
            *podman*)
                continue ;;
            'exit code'*)
                continue ;;
        esac
        docker ps -a --format='{{.Names}} {{.Status}}' --filter id=${id}
    done | while read name status rest ; do
        if valid_module_name ${name} ; then
            echo "OM_COMP_STATUS_${name}=${status}" >>${TMPDIR}/compose_info
            echo "OM_COMP_NAMES=\"\${OM_COMP_NAMES} ${name}\"" >>${TMPDIR}/compose_info
        fi
        case ${name} in
            *_amieadmin_*)
                prefix=`expr "${name}" : '\(.*\)_amieadmin_.*'`
                suffix=`expr "${name}" : '.*_amieadmin_\(.*\)'`
                echo "OM_PREFIX=${prefix}" >>${TMPDIR}/compose_info
                echo "OM_SUFFIX=${suffix}" >>${TMPDIR}/compose_info
                echo "OM_ADMIN_NAME=${name}" >>${TMPDIR}/compose_info ;;
            *_amie_*)
                prefix=`expr "${name}" : '\(.*\)_amie_.*'`
                suffix=`expr "${name}" : '.*_amie_\(.*\)'`
                echo "OM_PREFIX=${prefix}" >>${TMPDIR}/compose_info
                echo "OM_SUFFIX=${suffix}" >>${TMPDIR}/compose_info
                echo "OM_AMIE_NAME=${name}" >>${TMPDIR}/compose_info ;;
        esac
    done
}

valid_module_name() {
    name="$1"
    invalid_name=`expr "${name}" : '.*\([^a-zA-Z0-9_]\).*'`
    if [ ":${invalid_name}" = ":" ] ; then
        return 0
    fi      
    return 1
}

kick() {
    log "Running 'docker-compose up -d'..."
    docker-compose up -d

    sleep 2
    return ${RC_OK}
}

bounce() {
    log "Running 'docker-compose down'..."
    docker-compose down
    
    sleep 2

    rotate_logs
    err=$?
    
    log "Running 'docker-compose up -d'..."
    docker-compose up -d

    sleep 2

    if [ $err != 0 ] ; then
        return ${RC_ERR}
    fi
    return ${RC_OK}
}

check_container_status() {
    . ${TMPDIR}/compose_info

    rc=0
    for name in ${OM_COMP_NAMES} ; do
        eval status="\"\${OM_COMP_STATUS_${name}}\""
        if [ ":${status}" != ":Up" ] ; then
            log "Container ${name} status is \"${status}\""
            rc=1
        fi
    done

    return $rc
}

rotate_logs() {
    # This assumes containers are down
    if [ ":${LOG_DIR}" != ":" ] && [ -d "${LOG_DIR}" ] ; then
        ${ROTATE_LOGS} ${LOG_DIR}
        return $?
    fi
    return 0
}

send_report() {
    rc=$1
    status=
    case ${rc} in
        ${RC_OK})
            : ;;
        ${RC_WARN})
           status=Note ;; 
        ${RC_ERR})
            status="ERROR NOTICE" ;;
    esac
    host=`hostname`
    subject="$status from amie-sam-mediator on $host"

    echo ${MAILER} ${MAIL_ARGS} -s "${subject}" ${EMAIL_ADDR} "<${REPORT}"
    if [ ":${DEBUG_OPS_MONITOR}" = ":" ] ; then
        cp ${LOG} ${REPORT}
        ${MAILER} ${MAIL_ARGS} -s "${subject}" ${EMAIL_ADDR} <${REPORT}
    else
        echo "(email suppressed)" >&2
    fi
    rm -f ${REPORT}
}

main
