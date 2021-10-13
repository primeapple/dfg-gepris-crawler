#!/bin/bash
set -a
source .env
set +a
# enable outside access of database
export POSTGRES_PORT=$POSTGRES_PORT_EXT
export POSTGRES_HOST=$POSTGRES_HOST_EXT
# disable mail logging
unset LOGGING_EMAIL_USERNAME
unset LOGGING_EMAIL_PASSWORD
unset LOGGING_EMAIL_SMTP_SERVER
unset LOGGING_EMAIL_SMTP_PORT
unset LOGGING_EMAIL_RECEIVER
unset LOGGING_EMAIL_SENDER
unset ADMINER_PORT_EXT
