

# App Rating Analytics

The project contains code related to App Rating Analytics.

* Extract the app ratings
* Aggregate the ratings by date, platform (iOS, Android) and rating
* Compare the aggregated overall rating of the current day with the historical trend(last 7 days)
* Enrichment flag added for “Customer Rating Increased” or “Customer Rating Declined”
* Consolidate the data and persist it in a relational database (Postgres)


## Design

![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/design.png)

## Tech Stack

![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/design-tech.png)

## Installation

Follow these steps to install the necessary tools.

1. Install [Docker Community Edition (CE)](https://docs.docker.com/engine/installation/) on your workstation. Depending on the OS, you may need to configure your Docker instance to use 4.00 GB of memory for all containers to run properly. Please refer to the Resources section if using [Docker for Windows](https://docs.docker.com/docker-for-windows/#resources) or [Docker for Mac](https://docs.docker.com/docker-for-mac/#resources) for more information.
2. Install [Docker Compose](https://docs.docker.com/compose/install/) v1.27.0 and newer on your workstation.

### Before you begin

Checkout the codebase: `git@github.com:dmanojbabu/app-rating-analytics.git` and change current directory to `app-rating-analytics`

Follow the steps to build the docker image required.

1. Image for Airflow with additional nodejs and python packages.
	```bash
	docker build -t manoj/docker-airflow .
	```
	
2. Image for [AppTweak](https://www.apptweak.io/documentation/ios/application_ratings) mock API.
	```bash
	docker build -t manoj/ratings-api ./ratings-mock-api
	```
	
3. Image for Jupyter Notebook with additional python packages.
	```bash
	docker build -t manoj/jupyter-notebook ./jupyter-notebook
	```

### Initializing Environment

Follow the steps to initialize the application environment.

Before starting the application for the first time, You need to prepare your environment, i.e. create the necessary files, directories and initialize the database.

Some directories in the container are mounted, which means that their contents are synchronized between your computer and the container.

- `./dags` - Application DAG files will be here.
- `./logs` - contains logs from task execution and scheduler, get created by itself.
- `./plugins` - you can put your [custom plugins](https://airflow.apache.org/docs/apache-airflow/stable/plugins.html) here, get created by itself.
- `./work` - Application sepecific Jupyter Notebook files present here.

On all operating systems, you need to run database migrations and create the first user account, related to Airflow. To do it, run.

```
docker-compose up airflow-init
```

After initialization is complete, you should see a message like below.

```
airflow-init_1       | Upgrades done
airflow-init_1       | Admin user airflow created
airflow-init_1       | 2.0.2
start_airflow-init_1 exited with code 0
```

The account created has the login **airflow** and the password **airflow**

## Running the application


To run the application use Docker-Compose with below command and It will create required services for running the application.

```bash
docker-compose up
```

In the second terminal you can check the condition of the containers.

![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/containers-init.PNG)

#### Container Services

The below container services are required for running the application.

1. `app-rating-analytics-airflow-scheduler_1`,  `app-rating-analytics-airflow-webserver_1` required for running the [Airflow](https://airflow.apache.org/) scheduler and webserver components.
2. `app-rating-analytics_notebook_1` container runs the [Jupyter](https://jupyter.org/) a web based interactive IDE to access database and object-store.
3. `app-rating-analytics_ratingsapi_1` container runs MockAPI service an Express - Node.js app to serve as a mock API.
4. `app-rating-analytics_minio_1` container runs [MinIO](https://min.io/) an S3 compatible object storage.
5. `app-rating-analytics_postgres_1` container runs [PostgreSQL](https://www.postgresql.org/) for storing the Airflow metadata and storing the ratings aggregated result for serving.

### Accessing the environment

After the containers are started correctly, the environments can be accessed as below.

1. Access the Airflow web interface at at: `http://localhost:8080`. 
2. The default account has the login `airflow` and the password `airflow`. 

#### Trigger the workflow from Airflow

Trigger the workflow DAG created in Airflow to execute the sequence of  steps to perform the analytics.

1. Enable the DAG `app_rating_elt` from UI from Airflow home page

   ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/dag-enable.PNG)

2. Trigger the DAG `app_rating_elt` from the Actions on top right side of Airflow UI.   

   ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/dag-trigger.PNG)

   - After clicking the Trigger button provide the the configuration  `{ "sd": "2021-04-01", "ed": "2021-04-11"}` 
   - Then click the Trigger Button below.

3. Monitor the UI for the progress of steps completion.

   1. Top open the DAG  click the DAG name `app_rating_elt` and it will show the steps and click  `Graph View` for better view.

      ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/dag-graph.PNG)

   2. To check the logs of particular step in dag from `Graph View` click a step.

      1. click `extract_ratings` step to view its execution log.

         ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/dag-step-log.PNG)

   3. After steps are executed successfully as below then we can view the results from exported table.

      ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/dag-success.PNG)

### Accessing the results

After the workflow execution is completed all the steps successfully in Airflow then we can query data using `SQL` from the `Jupyter` Notebook provided.

1. To access the `Jupyter` Notebook need to fetch the access token from docker container logs as below.

   - Execute `docker ps` command to find the `Container Id` of image `manoj/jupyter-notebook` 

     ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/jupyter-container-id.PNG)

   - Using the `Container Id` check the logs of the container for access token URL.

     ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/jupyter-token.PNG)

   - Use the Jupyter URL with access token from logs to access `Jupyter` web interface and open the Notebook `product-leader.ipynb` from the folder `work`. 

     ![](https://raw.githubusercontent.com/dmanojbabu/app-rating-analytics/main/img/jupyter-results.PNG)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)