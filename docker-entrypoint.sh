#!/bin/sh

chown -R nonroot:nonroot database/sqlite
gosu nonroot gunicorn eventfully.main:app -w 4 -b 0.0.0.0:8000