from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, union, cast, dropna ,lit, to_date, sum as spark_sum, mean as spark_mean, udf
from pyspark.sql.types import TimestampType, IntegerType,StructType, StructField, StringType, FloatType, DateType
from pyspark.sql.functions import date_format, when, regexp_replace, trim, date_trunc
from pyspark.sql.window import Window
from pyspark.sql.functions import dense_rank, rand
from datetime import datetime, timedelta
from pyspark.sql import functions as F
from pyspark.sql.functions import col, to_date, date_add, date_sub, expr
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import numpy as np

def create_spark_session():
    spark = SparkSession.builder \
        .appName("Data Processing") \
        .getOrCreate()
    return spark

def load_data(spark):

    post = spark.read.parquet("your s3 path")
    comment = spark.read.parquet("your s3 path")
    issue = spark.read.parquet("your s3 path")
    word_freq = spark.read.parquet("your s3 path")
    live_post = spark.read.parquet("your s3 path")
    live_comment = spark.read.parquet("your s3 path")
    
    return post, comment, issue, word_freq, live_post, live_comment


def preprocess_data(post_df, comment_df):

    post_df = post_df.withColumn("DateTime", col("DateTime").cast(TimestampType())) \
                     .withColumn("ViewCount", col("ViewCount").cast(IntegerType()))
    comment_df = comment_df.withColumn("DateTime", col("DateTime").cast(TimestampType()))
    post_df = post_df.withColumn("DateTime", to_timestamp("DateTime")) \
                     .withColumn("DateTime", (col("DateTime").cast("long") / 3600).cast("long") * 3600) \
                     .withColumn("DateTime", to_timestamp(col("DateTime")))
    comment_df = comment_df.withColumn("DateTime", to_timestamp("DateTime"))
    post_df = post_df.dropna(subset=["ViewCount", "DateTime"])

    return post_df, comment_df

#24시간 간격으로 post와 comment 데이터를 집계(일별로 묶기)
def aggregate_data(post, comment):

    score = post.groupBy(F.window(col("DateTime"), "24 hours"), "CarName") \
                .agg(F.sum("ViewCount").alias("ViewCount"),
                     F.count("CarName").alias("post_count")) \
                .withColumn("DateTime", col("window.start")).drop("window")

    comment_count = comment.groupBy(F.window(col("DateTime"), "24 hours"), "CarName") \
                           .agg(F.count("*").alias("comment_count")) \
                           .withColumn("DateTime", col("window.start")).drop("window")

    combined_score = score.join(comment_count, ["DateTime", "CarName"], "left") \
                          .fillna({"comment_count": 0}) \
                          .withColumn("ViewCount", F.when(col("ViewCount") <= 0, 1).otherwise(col("ViewCount"))) \
                          .withColumn("post_count", F.when(col("post_count") <= 0, 1).otherwise(col("post_count"))) \
                          .withColumn("comment_count", F.when(col("comment_count") < 0, 0).otherwise(col("comment_count"))) \
                          .filter(col("DateTime") >= "2015-01-01")

    return combined_score


# 점수를 계산하고 이상치를 처리하며 최종 점수를 정규화
def calculate_scores(score):
    score = score.withColumn("score", (col("ViewCount") / col("post_count")) + col("post_count") * 10 + col("comment_count"))
    percentile95 = score.approxQuantile("score", [0.95], 0.01)[0]
    score = score.withColumn("score", F.when(col("score") > percentile95, percentile95).otherwise(col("score")))

    min_score, max_score = score.select(F.min("score"), F.max("score")).first()
    score = score.withColumn("score", ((col("score") - min_score) / (max_score - min_score)) * 100)

    return score

def optimize(df, num_partitions=4):
    return df.repartition(num_partitions)

#'post'와 'comment' 데이터 프레임을 병합하고 감정별로 데이터를 집계 및 분석
def merge_and_analyze_sentiments(post, comment):
    combined = post.select("DateTime", "CarName", "SentimentCategory")\
                   .union(comment.select("DateTime", "CarName", "SentimentCategory"))

    sentiment_count = combined.groupBy("DateTime", "CarName", "SentimentCategory")\
                              .count()\
                              .groupBy("DateTime", "CarName")\
                              .pivot("SentimentCategory", ["Negative", "Neutral", "Positive"])\
                              .sum("count")\
                              .na.fill(0) 
    
    total = col("Negative") + col("Neutral") + col("Positive")
    for category in ["Negative", "Neutral", "Positive"]:
        sentiment_count = sentiment_count.withColumn(category, col(category) / total)

    # 2015년 1월 1일 이후 데이터 필터링
    sentiment_count = sentiment_count.filter(col("DateTime") >= "2015-01-01")

    return sentiment_count

def calculate_dtw_udfs(base_scores, other_scores):
    base_scores = np.array(base_scores).flatten().tolist() if isinstance(base_scores[0], list) else base_scores
    other_scores = np.array(other_scores).flatten().tolist() if isinstance(other_scores[0], list) else other_scores
    
    distance, _ = fastdtw(base_scores, other_scores, dist=2)
    return float(distance)

def calculate_similarity_with_dtw(score, issue, base_car, base_date):

    issue = issue.withColumn("DateTime", to_timestamp(col("DateTime"), "yyyy.M.d"))
    base_scores_collected = score.filter(
        (col("CarName") == base_car) &
        (col("DateTime") >= (base_date - timedelta(days=3))) &
        (col("DateTime") < base_date)
    ).agg(collect_list("score").alias("base_scores"))

    base_data_with_scores = score.filter(
        (col("CarName") == base_car) &
        (col("DateTime") >= (base_date - timedelta(days=3))) &
        (col("DateTime") < base_date)
    ).crossJoin(base_scores_collected)

    window_spec = Window.partitionBy("CarName").orderBy("DateTime")
    score_windowed = score.filter(col("CarName") != base_car) \
        .withColumn("row_number", F.row_number().over(window_spec)) \
        .withColumn("group_id", F.floor((col("row_number") - 1) / 3)) \
        .groupBy("CarName", "group_id") \
        .agg(F.collect_list("score").alias("score_window"),
             F.min("DateTime").alias("SimilarDate")) \
        .withColumn("end_date", F.date_add(col("SimilarDate"), 2))

    joined_data = score_windowed.alias("a").join(
        score.alias("b"),
        (col("a.CarName") == col("b.CarName")) &
        (col("b.DateTime") >= col("a.SimilarDate") - expr("interval 3 days")) &
        (col("b.DateTime") <= col("a.end_date")),
        "inner"
    ).select("a.CarName", "a.score_window", "b.score", "a.SimilarDate")

    closest_issue_date = joined_data.alias("jd").join(
        issue.alias("issue"),
        (col("jd.CarName") == col("issue.CarName")) &
        (col("issue.DateTime") >= expr("date_sub(jd.SimilarDate, 14)")) &
        (col("issue.DateTime") <= col("jd.SimilarDate")),
        "left_outer"
    ).groupBy("jd.CarName", "jd.SimilarDate").agg(
        spark_min("issue.DateTime").alias("ClosestIssueDate")
    )

    joined_data_with_issues = joined_data.join(
        closest_issue_date,
        ["CarName", "SimilarDate"],
        "left"
    )

    similarity_results_df = base_data_with_scores.alias("base").crossJoin(joined_data_with_issues.alias("joined")) \
        .withColumn("DTW_distance", calculate_dtw_spark(col("base.base_scores"), col("joined.score_window"))) \
        .withColumn("Similarity", 100 - col("DTW_distance")) \
        .select(
            col("base.CarName").alias("BaseCar"),
            col("base.DateTime").alias("BaseDate"),
            col("joined.CarName").alias("SimilarCar"),
            col("joined.SimilarDate"),
            col("joined.ClosestIssueDate"),
            col("Similarity")
        )

    similarity_raw = similarity_results_df.filter(col("Similarity") >= 1)
    window_spec = Window.orderBy(col("priority").asc(), col("Similarity").desc())

    similarity_with_priority = similarity_raw.withColumn(
        "priority", 
        when(col("ClosestIssueDate").isNotNull(), 1).otherwise(2)
    )
    similarity = (similarity_with_priority
                  .withColumn("rank", row_number().over(window_spec))
                  .filter(col("rank") <= 10)
                  .drop("rank")
                  .orderBy(col("priority").asc(), col("Similarity").desc()))

    return similarity

# 유사도 기반 필터링 수행
def filter_and_merge_dataframes(similarity, score, post, sentiment_count, issue, word_freq):
    # 결과를 저장할 리스트 초기화
    filtered_score = []
    filtered_post = []
    filtered_sentiment_count = []
    filtered_issues = []
    filtered_word_freq = []

    top_similarity_rows = similarity.collect()

    for row in top_similarity_rows:
        similar_car = row['SimilarCar']
        similar_date = row['SimilarDate']

        start_date = similar_date - timedelta(days=7)
        end_date = similar_date + timedelta(days=7)

        filtered_score_data = score.filter(
            (col('CarName') == similar_car) &
            (col('DateTime') >= start_date) &
            (col('DateTime') <= end_date)
        )
        filtered_score.append(filtered_score_data)

        filtered_post_data = post.filter(
            (col('CarName') == similar_car) &
            (col('DateTime') >= start_date) &
            (col('DateTime') <= end_date)
        )

        window_spec = Window.partitionBy("CarName", to_date("DateTime")).orderBy(col("ViewCount").desc())
        filtered_post_data = filtered_post_data.withColumn("row_number", F.row_number().over(window_spec)) \
                                               .filter(col("row_number") == 1).drop("row_number")
        filtered_post.append(filtered_post_data)
        filtered_sentiment_count_data = sentiment_count.filter(
            (col('CarName') == similar_car) &
            (col('DateTime') >= start_date) &
            (col('DateTime') <= end_date)
        )
        filtered_sentiment_count.append(filtered_sentiment_count_data)
        filtered_issues_data = issue.filter(
            (col('CarName') == similar_car) &
            (col('DateTime') >= start_date) &
            (col('DateTime') <= end_date)
        )
        filtered_issues.append(filtered_issues_data)
        filtered_word_freq_df = word_freq.filter((col("CarName") == similar_car) & 
                                                 (to_date(col("Date")) >= start_date) & 
                                                 (to_date(col("Date")) <= end_date))
        filtered_word_freq.append(filtered_word_freq_df)

    filtered_dataframes = {}

    if filtered_score:
        filtered_dataframes['filtered_score'] = reduce(lambda df1, df2: df1.union(df2), filtered_score)
    
    if filtered_post:
        filtered_dataframes['filtered_post'] = reduce(lambda df1, df2: df1.union(df2), filtered_post)

    if filtered_sentiment_count:
        filtered_dataframes['filtered_sentiment_count'] = reduce(lambda df1, df2: df1.union(df2), filtered_sentiment_count)

    if filtered_issues:
        filtered_dataframes['filtered_issues'] = reduce(lambda df1, df2: df1.union(df2), filtered_issues)

    if filtered_word_freq:
        filtered_dataframes['filtered_word_freq'] = reduce(lambda df1, df2: df1.union(df2), filtered_word_freq)

    return filtered_dataframes

def save_dataframe_to_s3(df, s3_path, df_name):
    try:
        df.write.mode('overwrite').parquet(s3_path)
        print(f"{df_name} DataFrame saved to {s3_path}")
    except Exception as e:
        print(f"Error saving {df_name} to {s3_path}: {e}")


def main():
    spark = create_spark_session()
    post, comment, issue, word_freq, live_post, live_comment = load_data()
    post, comment = preprocess_data(post, comment)
    post = optimize(post)
    comment = optimize(comment)
    score = aggregate_data(post, comment)
    score = calculate_scores(score)
    sentiment_count = merge_and_analyze_sentiments(post,comment)
    base_car='tucson'
    base_date= base_date = datetime.now().date()
    score = score.repartition(6)
    issue = issue.repartition(6)
    similarity = calculate_similarity_with_dtw(spark, score, issue)
    score = score.repartition(4)
    issue = issue.repartition(4)

    filtered_dataframes = filter_and_merge_dataframes(similarity, score, post, sentiment_count, issue, word_freq)

    # 각 데이터프레임에 대한 S3 경로 설정
    s3_paths_dict = {
        'filtered_score': 's3://your-bucket-name/path/to/save/filtered_score/',
        'filtered_post': 's3://your-bucket-name/path/to/save/filtered_post/',
        'filtered_sentiment_count': 's3://your-bucket-name/path/to/save/filtered_sentiment_count/',
        'filtered_issues': 's3://your-bucket-name/path/to/save/filtered_issues/',
        'filtered_word_freq': 's3://your-bucket-name/path/to/save/filtered_word_freq/'
    }

    # 데이터프레임을 각각의 S3 경로에 저장
    for df_name, s3_path in s3_paths_dict.items():
        if df_name in filtered_dataframes:
            save_dataframe_to_s3(filtered_dataframes[df_name], s3_path, df_name)



if __name__ == "__main__":
    main()
