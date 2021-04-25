import time
from pprint import pprint

from airflow import DAG
from airflow.operators.python import PythonOperator, PythonVirtualenvOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from rating_store_ingest import RatingStoreIngest
from rating_agg_ingest import RatingAggIngest

args = {
    'owner': 'airflow',
}

with DAG(
    dag_id='app_rating_elt',
    default_args=args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['example'],
) as dag:

    def execute_store_ingest(ds, **kwargs):
        sd = kwargs['dag_run'].conf['sd']
        ed = kwargs['dag_run'].conf['ed']
        print("execute_store_ingest for sd:{0} and ed:{1}".format(sd, ed))
        app = RatingStoreIngest(sd, ed)
        app.start()

    def execute_agg_ingest(ds, **kwargs):
        sd = kwargs['dag_run'].conf['sd']
        ed = kwargs['dag_run'].conf['ed']
        print("execute_agg_ingest for sd:{0} and ed:{1}".format(sd, ed))
        app = RatingAggIngest(sd, ed)
        df = app.agg()
        app.ingest(df)

    def print_context(ds, **kwargs):
        """Print the Airflow context and ds variable from the context."""
        pprint(kwargs)
        print(ds)
        return 'Whatever you return gets printed in the logs'

    t1_extract_ratings = BashOperator(task_id='extract_ratings',
                                         bash_command='/opt/airflow/dags/extract_rating/runExtract.sh -s {{ dag_run.conf.sd }} -e {{ dag_run.conf.ed }}')

    t2_agg_app_ratings = PythonOperator(task_id='rating_store_ingest',
                                        python_callable=execute_store_ingest)

    t3_load_ratings = PythonOperator(task_id='rating_agg_ingest',
                                     python_callable=execute_agg_ingest)

    t1_extract_ratings >> t2_agg_app_ratings >> t3_load_ratings