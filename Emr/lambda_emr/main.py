import json
import pymysql
import boto3
import pandas as pd
from io import BytesIO
from sqlalchemy import create_engine

def get_db_connection(host, user, password, db):
    return pymysql.connect(host=host, user=user, password=password, db=db, charset='utf8')

def insert_data_from_dataframe(df, table_name, engine):
    df.to_sql(table_name, engine, if_exists='append', index=False)

def delete_all_data_from_table(host, user, password, database, table_name, connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name};")
            connection.commit() 
            print(f"All data from {table_name} has been deleted.")
    except Exception as e:
        print(f"Error occurred: {e}")


def create_engine_connection(host, user, password, db):
    database_url = f"mysql+pymysql://{user}:{password}@{host}/{db}"
    engine = create_engine(database_url)
    return engine


def read_csv_from_s3(bucket, key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    csv_content = response['Body'].read()
    return pd.read_csv(BytesIO(csv_content))


def get_files_from_folder(bucket, prefix):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    file_paths = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            file_paths.append(obj['Key'])
    return file_paths


def combine_csv_files(bucket, prefix):
    files = get_files_from_folder(bucket, prefix)
    dataframes = []
    for file in files:
        if file.endswith('.csv'):  
            df = read_csv_from_s3(bucket, file)
            dataframes.append(df)
    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df


def lambda_handler(event, context):

    bucket_name = 'bucket name'
    WordFrequency_path = 'your s3 path'
    SentimentCount_path = 'your s3 path'
    Similarity_path = 'your s3 path'
    Score_path = 'your s3 path'
    Posts_path = 'your s3 path'
    Issues_path = 'your s3 path'

    WordFrequency = combine_csv_files(bucket_name, WordFrequency_path)
    SentimentCount= combine_csv_files(bucket_name, SentimentCount_path)
    Similarity= combine_csv_files(bucket_name, Similarity_path)
    Score = combine_csv_files(bucket_name, Score_path)
    Posts = combine_csv_files(bucket_name, Posts_path)
    Issues = combine_csv_files(bucket_name, Issues_path)

    replacement_dict = {
        'kona': '코나',
        'casper':'캐스퍼' ,
        'santafe' : '싼타페',
        'venue' : '베뉴',
        'tucson' : '투싼',
        'palisade' : '팰리세이드',
        'sportage' : '스포티지'
    }
    WordFrequency['CarName'] = WordFrequency['CarName'].replace(replacement_dict)
    SentimentCount['CarName'] = SentimentCount['CarName'].replace(replacement_dict)
    Similarity['BaseCar'] = Similarity['BaseCar'].replace(replacement_dict)
    Similarity['SimilarCar'] = Similarity['SimilarCar'].replace(replacement_dict)
    Score['CarName'] = Score['CarName'].replace(replacement_dict)
    Posts['CarName'] = Posts['CarName'].replace(replacement_dict)
    Issues['CarName'] = Issues['CarName'].replace(replacement_dict)


    # RDS 접속 정보 설정
    db_host = "db host"
    db_user = "user name"  # RDS 사용자 이름
    db_password = "user pw"  # RDS 비밀번호
    db_name = "db name"  # 실제 사용할 데이터베이스 이름
    engine = create_engine_connection(db_host,db_user,db_password,db_name)
    connection = get_db_connection(db_host, db_user, db_password, db_name)

    delete_all_data_from_table(db_host, db_user, db_password, db_name, 'WordFrequency', connection)
    insert_data_from_dataframe(WordFrequency, 'WordFrequency', engine)

    delete_all_data_from_table(db_host, db_user, db_password, db_name, 'SentimentCount', connection)
    insert_data_from_dataframe(SentimentCount, 'SentimentCount', engine)

    delete_all_data_from_table(db_host, db_user, db_password, db_name, 'Similarity', connection)
    insert_data_from_dataframe(Similarity, 'Similarity', engine)

    delete_all_data_from_table(db_host, db_user, db_password, db_name, 'Score', connection)
    insert_data_from_dataframe(Score, 'Score', engine)

    delete_all_data_from_table(db_host, db_user, db_password, db_name, 'Issues', connection)
    insert_data_from_dataframe(Issues, 'Issues', engine)


    connection.close()

    return {
        "statusCode": 200,
        "body": "EMR Data upload to RDS"
    }



    
