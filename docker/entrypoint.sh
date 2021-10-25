#!/bin/sh
scrapyd-deploy production && exec "$@"
