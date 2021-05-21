from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.google.cloud.operators.cloud_build import CloudBuildCreateBuildOperator
import os
from pathlib import Path

pathScript = "/opt/airflow/dags/etl_scripts"
pathIris =  "/opt/airflow/dags/etl_scripts/featurestore/iris.txt"
pathEncoder = "/opt/airflow/dags/etl_scripts/featurestore/irisEncoder.txt"
pathDeploy = "/opt/airflow/dags/deployApi/apiIris"
pathModel = "/opt/airflow/dags/deployApi/apiIris/model.pkl"

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "robotic-tide-284315")
CURRENT_FOLDER = Path().resolve()

default_args = {
   'owner': 'teste',
   'depends_on_past': False,
   'start_date': datetime(2019, 1, 1),
   'retries': 0,
   }


with DAG(
   'dag-pipeline-iris-aula-v3',
   schedule_interval=timedelta(minutes=10),
   catchup=False,
   default_args=default_args
   ) as dag:

    start = DummyOperator(task_id="start")

    with TaskGroup("etl", tooltip="etl") as etl:
        
        t1 = BashOperator(
            dag=dag,
            task_id='download_dataset',
            bash_command="""
            cd {0}/featurestore
            curl -o iris.txt  https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data
            """.format(pathScript)
        )

        [t1]

    with TaskGroup("preProcessing", tooltip="preProcessing") as preProcessing:
        t2 = BashOperator(
            dag=dag,
            task_id='encoder_dataset',
            bash_command="""
            cd {0}
            python etl_preprocessing.py {1} {2}
            """.format(pathScript, pathIris, pathEncoder)
        )
        [t2]

    with TaskGroup("model", tooltip="model") as model:
        t3 = BashOperator(
            dag=dag,
            task_id='modelo',
            bash_command="""
            cd {0}
            python ml_sklearn.py {1} {2} {3} {4} {5}
            """.format(pathScript,pathEncoder, "IrisClassificacao", "ModeloIris", 2, 0)
        )
        [t3]

    with TaskGroup("validate", tooltip="validate") as validate:
        t4 = BashOperator(
            dag=dag,
            task_id='validate',
            bash_command="""
            cd {0}
            python validateModel.py {1} {2}
            """.format(pathScript,"IrisClassificacao", pathModel)
        )
        [t4]

    with TaskGroup("buildImage", tooltip="buildImage") as buildImage:

        t5 = CloudBuildCreateBuildOperator(
                dag=dag,
                task_id='buildImage',
                project_id='robotic-tide-284315',
                body='/opt/airflow/dags/deployApi/apiIris/cloudbuild.yaml',
                gcp_conn_id='my_gcp_connection',
                api_version='v1',
                params={'name': 'Airflow'}
        )
        [t5]


    end = DummyOperator(task_id='end')

    start >> etl >> preProcessing >> model >> validate >> buildImage >> end