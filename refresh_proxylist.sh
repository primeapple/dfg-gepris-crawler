#!/bin/bash
if [ -z ${WEBSHARE_PROXY_LIST_URL+x} ];
  then exit 1;
fi;
FILENAME=".proxylist.txt"
curl -o $FILENAME $WEBSHARE_PROXY_LIST_URL
sed -r -i '' 's|(.*):(.*):(.*):(.*)\r|http://\3:\4@\1:\2|' $FILENAME