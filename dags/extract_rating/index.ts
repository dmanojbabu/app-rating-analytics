import axios from 'axios';
import { AppRatings, RatingsEntity } from './model';
import { eachDayOfInterval, addDays, format } from 'date-fns';
import { S3 } from 'aws-sdk';
import * as dotenv from "dotenv";
import { Stream } from "stream";
import highland = require("highland");
import { getopt } from 'stdio';
import { GetoptResponse } from 'stdio/dist/getopt';

dotenv.config();

const IOS_URL = process.env.RATINGS_API_HOST + '/ios/applications/284882215/ratings.json';
const ANDROID_URL = process.env.RATINGS_API_HOST + '/android/applications/com.king.candycrushsaga/ratings-history.json';
const S3_BUCKET_NAME = 'rating-store';

const options: GetoptResponse = getopt({
  startdate: { key: 's', description: 'extract ratings from start date (YYYY-MM-DD).', args: 1, required: true },
  enddate: { key: 'e', description: 'extract rating till end date (YYYY-MM-DD).', args: 1, required: true },
}) as GetoptResponse;

const s3 = new S3(
  {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    endpoint: process.env.END_POINT,
    s3ForcePathStyle: true, // needed with minio?
    signatureVersion: 'v4'
  }
);

interface Extractor {
  s3: S3;
  options: GetoptResponse;
}

class Extractor {
  constructor(s3: S3, options: GetoptResponse) {
    this.s3 = s3;
    this.options = options;
  }

  createBucketIFNotExist = async () => {
    console.log('createBucketIFNotExist 1');
    await this.s3.headBucket({ Bucket: S3_BUCKET_NAME }).promise().then(function (data) {
      console.log('Bucket exist already.');
    }).catch(async (err) => {
      console.log('Bucket not exist already. ' + err);
      await this.createBucket();
    });
    console.log('createBucketIFNotExist 2');
  }

  private createBucket = async () => {
    console.log('createBucket 1');
    await this.s3.createBucket({ Bucket: S3_BUCKET_NAME }).promise().then(function (data) {
      console.log('Bucket created.');
    }).catch((err) => {
      console.log('Error creating bucket: ' + err);
      throw new Error(err);
    });
    console.log('createBucket 2');
  }

  fetchAppRatings = async () => {
    console.log('fetchAppRatings 1');
    const startDate = this.options.startdate;
    const endDate = this.options.enddate;

    const msg = `fetchAppRating for start-date: ${startDate} and end-date: ${endDate}`
    console.log(msg);
    const iurl = `${IOS_URL}?start_date=${startDate}&end_date=${endDate}`
    const aurl = `${ANDROID_URL}?start_date=${startDate}&end_date=${endDate}`
    const apimsg = `APIs: ${iurl},  ${aurl}`
    console.log(apimsg);

    const fetchIosRatings = axios.get<AppRatings>(iurl);
    const fetchAndroidRatings = axios.get<AppRatings>(aurl);
    axios.all([fetchIosRatings, fetchAndroidRatings]).then(axios.spread((...responses) => {
      this.createRecords1(responses[0].data, responses[1].data);
      // use/access the results 
    })).catch(errors => {
      console.log(errors.toJSON());
    })
    console.log('fetchAppRatings 2');
  }

  private transform = (records: AppRatings, store: string): AppRatings => {
    const runDates = this.getRunDates();
    let ratings = records.content.ratings as RatingsEntity[];

    ratings.forEach((rating, index) => {
      let rec = rating;
      rec.date = runDates[index];
      rec.store = store;
    });
    return records
  }

  private createRecords1 = (iosrec: AppRatings, androidrec: AppRatings): void => {
    let iosRes = this.transform(iosrec, 'íos');
    console.log('No of iosRes extracted: ' + iosRes);
    let androidRes = this.transform(androidrec, 'android');
    console.log('No of androidRes extracted: ' + androidRes);
    let ratings = iosRes.content.ratings?.concat(androidRes.content.ratings!) as RatingsEntity[];    
    console.log('No of rating extracted: ' + ratings.length);
    var data = highland(ratings).map(function (rating) {
      return JSON.stringify(rating) + '\n';
    });

    //data.pipe(process.stdout);
    data.pipe(this.uploadFromStream());
  }

  private createRecords = (records: AppRatings): void => {
    var ratings: RatingsEntity[] = records.content.ratings as RatingsEntity[];
    console.log('No of rating extracted: ' + ratings.length);
    var data = highland(ratings).map(function (rating) {
      return JSON.stringify(rating) + '\n';
    });

    //data.pipe(process.stdout);
    data.pipe(this.uploadFromStream());
  }

  getRunDates = (): string[] => {
    let startDate = this.options.startdate as string;
    let endDate = this.options.enddate as string;
    const startd = addDays(new Date(startDate), +0);
    const endd = addDays(new Date(endDate), +0);
    return eachDayOfInterval({
      start: startd,
      end: endd
    }).map(d => format(d, 'yyyy-MM-dd'));
  }

  private uploadFromStream = () => {
    const endDate = this.options.enddate as string;
    var pass = new Stream.PassThrough();
    var params = { Bucket: S3_BUCKET_NAME, Key: endDate, Body: pass };
    this.s3.upload(params).promise().then(function (data) {
      console.log('Ratings uploaded to bucket.');
    }).catch(function (err) {
      console.log('Error uploading data to bucket. ' + err);
    });
    return pass;
  }
}

const app = async () => {
  try {
    const extractor = new Extractor(s3, options);
    await extractor.createBucketIFNotExist()
    await extractor.fetchAppRatings();
  } catch (e) {
    console.log('Error in running App: ', e);
  }
};

app();
