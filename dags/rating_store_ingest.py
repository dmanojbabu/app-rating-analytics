import boto3
from botocore.client import Config
import awswrangler as wr


BOTO_SESSION = boto3.Session(aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
                    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')
wr.config.s3_endpoint_url='http://minio1:9000'
S3_BUCKET = 'rating-store'


class RatingStoreIngest:
    """" RatingStoreIngest contains related methods to move data from staging area

         * Rename rating column names
         * Read json format data from staging and partition by date, store then persist data as parquet format
    """
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def start(self):
        """"Method to move date from staging and partition by date and persist """
        s3_path = 's3://{0}/{1}'.format(S3_BUCKET, self.end_date)
        print('RatingStoreIngest: read json data from stage path {0}'.format(s3_path))
        stage_df = wr.s3.read_json(s3_path, lines=True, boto3_session=BOTO_SESSION)
        print('RatingStoreIngest: shape of {0}'.format(stage_df.shape))

        # load required columns & index
        stage_df = stage_df[['1', '2', '3', '4', '5', 'date', 'store']]
        stage_df['date'] = stage_df['date'].dt.strftime('%Y-%m-%d')
        stage_df["rating_date"] = stage_df['date']
        stage_df.set_index('date', inplace=True)

        # rename column names
        stage_df = stage_df.rename(columns={"1": "R1", "2": "R2", "3": "R3", "4": "R4", "5": "R5"})
        stage_df.head()

        s3_pq_path = 's3://{0}/{1}/'.format(S3_BUCKET, 'ratings-pq')
        print('RatingStoreIngest: write data in parquet format to path {0}'.format(s3_pq_path))
        wr.s3.to_parquet(
            df=stage_df,
            path=s3_pq_path,
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=['rating_date', 'store'],
            boto3_session=BOTO_SESSION
        )
        print('RatingStoreIngest: write data in parquet format completed.')
