import boto3
import awswrangler as wr
import pandas as pd
import datetime
import numpy as np
import sqlalchemy


BOTO_SESSION = boto3.Session(aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
                    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')
ENGINE = sqlalchemy.create_engine("postgresql://airflow:airflow@postgres/airflow")
wr.config.s3_endpoint_url='http://minio1:9000'
S3_BUCKET = 'rating-store'
PG_TABLE = 'app_ratings'


class RatingAggIngest:
    """ RatingAggIngest contains related methods to aggregate and ingest ratings

        * Aggregate the ratings by date, platform (iOS, Android) and rating
        * Compare the aggregated overall rating of the current day with the historical trend(last 7 days)
        * enrichment flag added for “Customer Rating Increased” or “Customer Rating Declined”
        * Consolidate the data and persist it in a relational database (Postgres)
    """
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def date_range(self, start, end):
        """"Method return date range based on start and end date """
        previous_day = start - datetime.timedelta(days=6)
        r = (end + datetime.timedelta(days=1) - previous_day).days
        return [str(previous_day + datetime.timedelta(days=i)) for i in range(r)]

    def path_filter(self, partitions):
        """Method to filter path based on start and end date, it will avoid reading whole data  """
        sd = datetime.datetime.strptime(self.start_date, '%Y-%m-%d').date()
        ed = datetime.datetime.strptime(self.end_date, '%Y-%m-%d').date()
        # print("filter sd:{0} and ed:{1}".format(sd, ed))
        date_list = self.date_range(sd, ed)
        return partitions['rating_date'] in date_list

    def rating_total(self, row):
        """Method to calculate total rating daily ratings columns """
        return row['R1'] + row['R2'] + row['R3'] + row['R4'] + row['R5'];

    def rating_total_L7d(self, row):
        """Method to calculate total rating for L7D columns """
        return row['R1 L7D'] + row['R2 L7D'] + row['R3 L7D'] + row['R4 L7D'] + row['R5 L7D'];

    def calculate_star_rating(self, row):
        """This function calculates the star rating of the given list with array positions as
        0 - 1 Star
        1 - 2 Stars
        2 - 3 Stars
        3 - 4 Stars
        4 - 5 Stars
        """
        rating_list = [row['R1 L7D'], row['R2 L7D'], row['R3 L7D'], row['R4 L7D'], row['R5 L7D']]
        stars = [1, 2, 3, 4, 5]
        return round(sum(list(map(lambda a, b: a * b, stars, rating_list))) / sum(rating_list), 2)

    def agg(self):
        """"Method to perform the agg transformation steps """
        s3_path = 's3://{0}/{1}'.format(S3_BUCKET, 'ratings-pq')
        print('RatingAggIngest: read parquet data from path {0}'.format(s3_path))
        # read the rating by filter based on start and end date
        rating_df = wr.s3.read_parquet(path=s3_path, boto3_session=BOTO_SESSION, dataset=True,
                                       partition_filter=self.path_filter)
        print('RatingAggIngest: shape of {0}'.format(rating_df.shape))

        # set index
        rating_df.set_index('rating_date', inplace=True)
        rating_df = rating_df.sort_index()

        # agg ratings
        agg_df = rating_df.groupby(['rating_date', 'store']).agg(
            {'R1': 'sum', 'R2': 'sum', 'R3': 'sum', 'R4': 'sum', 'R5': 'sum'})

        # rolling last 7 days agg
        _grouped = rating_df.groupby("store").rolling(7)['R1', 'R2', 'R3', 'R4', 'R5'].sum()
        df_7d_sum = pd.DataFrame(_grouped)
        df_7d_sum = df_7d_sum.dropna()

        # rename ratings as L7D
        df_7d_sum = df_7d_sum.rename(
            columns={"R1": "R1 L7D", "R2": "R2 L7D", "R3": "R3 L7D", "R4": "R4 L7D", "R5": "R5 L7D"})

        # merge ratings and L7D ratings
        result_df = agg_df.copy()
        result_df = result_df.merge(df_7d_sum, left_index=True, right_index=True)

        # derive avg and total
        result_df['avg_rating L7D'] = result_df.apply(lambda row: self.calculate_star_rating(row), axis=1)
        result_df['avg_rating'] = result_df.apply(lambda row: self.calculate_star_rating(row), axis=1)
        result_df['total'] = result_df.apply(lambda row: self.rating_total(row), axis=1)
        result_df['total L7D'] = result_df.apply(lambda row: self.rating_total_L7d(row), axis=1)

        # derive enrichment flag
        result_df['flag'] = np.where(result_df['avg_rating'] > result_df['avg_rating L7D'], 'Customer Rating Increased',
                                     'Customer Rating Declined')

        # filter required columns
        final_df = result_df[
            ['R1', 'R2', 'R3', 'R4', 'R5', 'total', 'total L7D', 'avg_rating', 'avg_rating L7D', 'flag']]
        print('RatingAggIngest: aggregation steps completed')
        return final_df

    def ingest(self, df):
        """"Method to ingest final data frame into database """
        print('RatingAggIngest: Ingestion started, shape of {0}'.format(df.shape))
        con = ENGINE.connect()
        df.to_sql(PG_TABLE, con, if_exists="append")
        print('RatingAggIngest: Ingestion completed.')
