'use strict';

const express = require('express');
//import { format, compareAsc } from 'date-fns'
const datefn = require('date-fns')

// Constants
const PORT = 5000;
const HOST = '0.0.0.0';

function getMockRatings(ratingsSize) {
  let mockRatings = new Array();
  let rating = {
    "1": 10,
    "2": 20,
    "3": 30,
    "4": 40,
    "5": 50,
    total: 150,
    avg: 4.44
  }
  for (let i = 0; i < ratingsSize; i++) {
    mockRatings.push(rating)
  }
  return mockRatings;
}

function getRunDates(startDate, endDate) {
  var startd = datefn.addDays(new Date(startDate), +0);
  var endd = datefn.addDays(new Date(endDate), +0);
  return datefn.eachDayOfInterval({
    start: startd,
    end: endd
  }).map(d => datefn.format(d, 'yyyy-MM-dd'));
}

const ratings = {
  content: {
    ratings: [
    ],
    start_date: "2018-11-10 00:00:00 +0000",
    end_date: "2018-11-15 00:00:00 +0000"
  },
  metadata: {
    request: {
      path: "/applications/com.king.candycrushsaga/ratings-history.json",
      store: "android",
      params: {
        start_date: "2018-11-10T00:00:00+00:00",
        end_date: "2018-11-15T00:00:00+00:00",
        id: "com.king.candycrushsaga",
        format: "json"
      },
      performed_at: "2018-11-27 01:30:43 UTC"
    },
    content: {

    }
  }
};

// App
const app = express();
app.get('/ios/applications/284882215/ratings.json', (req, res) => {
  var startDate = req.query['start_date']
  var endDate = req.query['end_date']
  var ratings = prepData(startDate, endDate, 'ios');
  res.json(ratings);
});

app.get('/android/applications/com.king.candycrushsaga/ratings-history.json', (req, res) => {
  var startDate = req.query['start_date']
  var endDate = req.query['end_date']
  var ratings = prepData(startDate, endDate, 'android');
  res.json(ratings);
});

function prepData(startDate, endDate, store) {
  var runDates = getRunDates(startDate, endDate)
  var mckRatings = getMockRatings(runDates.length)
  ratings.content.ratings = mckRatings
  ratings.content.start_date = new Date(startDate);
  ratings.content.end_date = new Date(endDate);
  ratings.metadata.request.params.start_date = new Date(startDate);
  ratings.metadata.request.params.end_date = new Date(endDate);
  ratings.metadata.request.performed_at = new Date();
  ratings.metadata.request.store = store;
  return ratings;
}

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);