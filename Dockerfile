FROM apache/airflow:2.0.2

USER root

ARG DEV_APT_COMMAND="\
    curl --fail --location https://deb.nodesource.com/setup_12.x | bash - \
    && curl https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - > /dev/null \
    && echo 'deb https://dl.yarnpkg.com/debian/ stable main' > /etc/apt/sources.list.d/yarn.list"

RUN bash -o pipefail -e -u -x -c "${DEV_APT_COMMAND}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
           nodejs \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install boto3 awswrangler pandas numpy sqlalchemy psycopg2-binary


