#!/bin/bash
CURRENTDIR=$(dirname "$0")
echo "Running $1"
case $1 in
  uvirun)
    uvicorn main:app --reload --host 0.0.0.0 --port 8101
    ;;
  celery)
    celery -A main.celery_app worker --loglevel=info
    ;;

  *)
    echo "unknown command received."
    exit 1;;
esac
