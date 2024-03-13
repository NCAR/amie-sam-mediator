ARG SWEET_QUAL=:latest
FROM ghcr.io/ncar/sweet${SWEET_QUAL}

ARG AMIEMEDIATOR_QUALIFIER=:latest
FROM ghcr.io/ncar/amiemediator${AMIEMEDIATOR_QUALIFIER}

COPY --from=0 /usr/local /usr/local/

ONBUILD USER root
USER root
RUN /usr/local/sweet/sbin/install-sweet-deps

ARG PACKAGE=amie-sam-mediator
ARG IMAGE=ghcr.io/ncar/amie-sam-mediator
ARG IMAGE_VERSION=snapshot
ARG BRANCH=main
ARG PACKAGE_DIR=/usr/local/amie-sam-mediator

#
# The amie-sam-mediator containers run as $SAMUSER.
#
ARG SAMUSER=tomcat-sam
ARG SAMUSERID=303
ARG SAMGROUP=tomcat-sam
ARG SAMGROUPID=303

ENV PACKAGE=amie-sam-mediator \
    PACKAGE_DIR=/usr/local/amie-sam-mediator \
    SAMUSER=${SAMUSER} \
    SAMUSERID=${SAMUSERID} \
    SAMGROUP=${SAMGROUP} \
    SAMGROUPID=${SAMGROUPID}

COPY bin ${PACKAGE_DIR}/bin/
COPY src ${PACKAGE_DIR}/src/
COPY gendoc-src ${PACKAGE_DIR}/
COPY run-all-tests gendoc-src \
     $PACKAGE_DIR/

RUN make-local-links /usr/local/sweet /usr/local ; \
    make-local-links ${PACKAGE_DIR} /usr/local ; \
    addgroup --gid ${SAMGROUPID} ${SAMGROUP} ; \
    adduser --disabled-password \
            --uid ${SAMUSERID} \
            --gid ${SAMGROUPID} \
            --gecos "SAM user" \
            --home /home/${SAMUSER} \
            --shell /bin/bash \
            $SAMUSER ; \
    sweet-build-init ${SAMUSERID}:${SAMGROUPID} ; \
    chown ${SAMUSER}:${SAMGROUP} /var/data
    
RUN cd ${PACKAGE_DIR} ; \
    /usr/local/sweet/bin/gendoc -v >gendoc/.log 2>&1 ; \
    chown -R $SAMUSER:$SAMGROUP gendoc

USER ${SAMUSER}:${SAMGROUP}

ENTRYPOINT [ "/usr/local/sweet/sbin/sweet-entrypoint.sh" ]

WORKDIR ${PACKAGE_DIR}

CMD [ "amie" ]


