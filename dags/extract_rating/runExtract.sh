#!/bin/bash
#ENV NPM_CONFIG_PREFIX=/tmp/.npm-global
#ENV PATH=$PATH:/tmp/.npm-global/bin # optionally if you want to run npm global bin without specifying path
cd $AIRFLOW_HOME/dags/extract_rating
npm install
# --prefix /opt/airflow

#npm install
#npm run start -- -s 2021-10-01 -e 2021-10-01

npm run start -- "$@"
