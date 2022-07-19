#!/bin/sh

echo "${BACKUP_CRON_EXPRESSION} python ${ROOT}/main.py >> /dev/stdout" > crontab.txt
crontab crontab.txt
/usr/sbin/crond -f -l 8
