import boto3
import pandas as pd
import io
from datetime import datetime
import json

def process_csv_from_s3(bucket_name, folder_path, output_bucket_name, output_folder):
    s3_client = boto3.client('s3')

    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
    csv_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.csv')]
    post_files = [file for file in csv_files if 'post' in file]
    comment_files = [file for file in csv_files if 'comment' in file]

    post_df_list = []
    comment_df_list = []

    for file_key in post_files:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        post_df_list.append(df)

    for file_key in comment_files:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        comment_df_list.append(df)

    post_df = pd.concat(post_df_list, ignore_index=True)
    comment_df = pd.concat(comment_df_list, ignore_index=True)

    year = "2024"

    def convert_datetime_format(date_str):
        try:
            if '.' in date_str:
                return datetime.strptime(f"{year}.{date_str}", "%Y.%m.%d %H:%M:%S")
            else:
                return pd.to_datetime(date_str)
        except Exception as e:
            return pd.NaT
        
    post_df['DateTime'] = post_df['DateTime'].apply(convert_datetime_format)
    comment_df['DateTime'] = comment_df['DateTime'].apply(convert_datetime_format)
    save_dataframe_to_s3(post_df, output_bucket_name, f"{output_folder}/processed_post.csv")
    save_dataframe_to_s3(comment_df, output_bucket_name, f"{output_folder}/processed_comment.csv")


def save_dataframe_to_s3(df, bucket_name, s3_path):

    s3_client = boto3.client('s3')
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=bucket_name, Key=s3_path, Body=csv_buffer.getvalue())
    print(f"DataFrame saved to {s3_path} in bucket {bucket_name}.")


def start_emr_cluster():

    emr_client = boto3.client('emr', region_name='ap-northeast-2')
    
    bootstrap_script_path = 's3://<your-bucket>/path-to-your-bootstrap-script.sh'

    # 부트스트랩 작업 정의
    bootstrap_actions = [
        {
            'Name': 'Install Libraries',
            'ScriptBootstrapAction': {
                'Path': bootstrap_script_path,
                'Args': []  
            }
        }
    ]
    
    # EMR 클러스터 생성
    cluster_response = emr_client.run_job_flow(
        Name='MyEMRCluster',
        ReleaseLabel='emr-6.3.0',  
        Applications=[{'Name': 'Spark'}],
        Instances={
            'InstanceGroups': [
                {
                    'Name': 'Master nodes',
                    'Market': 'ON_DEMAND',
                    'InstanceRole': 'MASTER',
                    'InstanceType': 'm5.xlarge',
                    'InstanceCount': 1,
                },
                {
                    'Name': 'Core nodes',
                    'Market': 'ON_DEMAND',
                    'InstanceRole': 'CORE',
                    'InstanceType': 'm5.xlarge',
                    'InstanceCount': 1,
                },
                {
                    'Name': 'Task nodes',
                    'Market': 'SPOT',
                    'InstanceRole': 'TASK',
                    'InstanceType': 'm5.xlarge',
                    'InstanceCount': 2,
                }
            ],
            'KeepJobFlowAliveWhenNoSteps': True,
            'TerminationProtected': False
        },
        BootstrapActions=bootstrap_actions,  
        Steps=[],
        LogUri='s3://<your-bucket>/logs/',  
        ServiceRole='<EMR_DefaultRole>',  
        JobFlowRole='<EMR_EC2_DefaultRole>', 
        VisibleToAllUsers=True
    )
    
    cluster_id = cluster_response['JobFlowId']
    
    step_args = [
        'spark-submit', 
        '--deploy-mode', 'cluster',
        's3://<your-bucket>/path-to-your-pyspark-script.py'
    ]
    
    step = {
        'Name': 'Process new data and load to Redshift',
        'ActionOnFailure': 'CONTINUE',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args': step_args
        }
    }
    
    response = emr_client.add_job_flow_steps(
        JobFlowId=cluster_id,
        Steps=[step]
    )
    
    print('EMR step added:', response['StepIds'][0])


def lambda_handler(event, context):

    bucket_name = '<your-input-bucket>'
    folder_path = '<your-input-folder>'
    output_bucket_name = '<your-output-bucket>'
    output_folder = '<your-output-folder>'
    
    process_csv_from_s3(bucket_name, folder_path, output_bucket_name, output_folder)
    
    start_emr_cluster()

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda function executed successfully!')
    }


