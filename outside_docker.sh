#!/bin/bash
set -a
source .env
set +a
# enable outside access of database
export POSTGRES_PORT=$POSTGRES_PORT_EXT
export POSTGRES_HOST=$POSTGRES_HOST_EXT
# disable proxies
unset WEBSHARE_PROXY_LIST_URL
# disable mail logging
#unset NOTIFICATION_EMAIL_USERNAME
#unset NOTIFICATION_EMAIL_PASSWORD
#unset NOTIFICATION_EMAIL_SMTP_SERVER
#unset NOTIFICATION_EMAIL_SMTP_PORT
#unset NOTIFICATION_EMAIL_RECEIVER
#unset NOTIFICATION_EMAIL_SENDER
# disable adminer
unset ADMINER_PORT_EXT
