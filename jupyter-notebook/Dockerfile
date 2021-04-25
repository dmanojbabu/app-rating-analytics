ARG BASE_CONTAINER=jupyter/minimal-notebook
FROM jupyter/minimal-notebook
LABEL author="Manoj"
USER root
RUN pip install boto3 awswrangler pandas numpy sqlalchemy psycopg2-binary ipython-sql
USER $NB_UID