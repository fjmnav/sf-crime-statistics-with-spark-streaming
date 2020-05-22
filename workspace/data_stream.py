import logging
import json
import os
from pyspark.sql import SparkSession
from pyspark.sql.types import *
import pyspark.sql.functions as psf


schema = StructType([
    StructField("crime_id", StringType(), True),
    StructField("original_crime_type_name", StringType(), True),
    StructField("report_date", TimestampType(), True),
    StructField("call_date", TimestampType(), True),
    StructField("offense_date", TimestampType(), True),
    StructField("call_time", StringType(), True),
    StructField("call_date_time", TimestampType(), True),
    StructField("disposition", StringType(), True),
    StructField("address", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("agency_id", StringType(), True),
    StructField("address_type", StringType(), True),
    StructField("common_location", StringType(), True)
])
"""
Data Example
{
      "crime_id": "183653763",
      "original_crime_type_name": "Traffic Stop",
      "report_date": "2018-12-31T00:00:00.000",
      "call_date": "2018-12-31T00:00:00.000",
      "offense_date": "2018-12-31T00:00:00.000",
      "call_time": "23:57",
      "call_date_time": "2018-12-31T23:57:00.000",
      "disposition": "ADM",
      "address": "Geary Bl/divisadero St",
      "city": "San Francisco",
      "state": "CA",
      "agency_id": "1",
      "address_type": "Intersection",
      "common_location": ""
    },
"""
def run_spark_job(spark):

    # TODO Create Spark Configuration
    # Create Spark configurations with max offset of 200 per trigger
    # set up correct bootstrap server and port
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
        .option("subscribe", "com.udacity.sf-crime.police.calls") \
        .option("startingOffserts", "earliest") \
        .option("maxOffsetsPerTrigger", 200) \
        .load()

    # Show schema for the incoming resources for checks
    #df.printSchema()

    # TODO extract the correct column from the kafka input resources
    # Take only value and convert it to String
    kafka_df = df.selectExpr("CAST(value AS STRING)")

    service_table = kafka_df \
        .select(psf.from_json(psf.col('value'), schema).alias("DF")) \
        .select("DF.*")

    # Print the records to make sure they are properly parsed
    # service_table.writeStream.format("console").start()

    # select original_crime_type_name and disposition
    distinct_table = service_table.select("original_crime_type_name", "disposition", "call_date_time")

    # count the number of original crime type
    agg_df = distinct_table.groupBy("original_crime_type_name") \
        .count() \
        .sort(psf.desc("count")) \
        .withWatermark('call_date_time', "1 minute")

    agg_df.printSchema()

    query = agg_df \
        .writeStream \
        .queryName("agg_query_writer") \
        .outputMode("Complete") \
        .format("console") \
        .start()
    
    
    # attach a ProgressReporter
    query.awaitTermination()

    radio_code_json_filepath = "radio_code.json"
    radio_code_df = spark.read.json(radio_code_json_filepath)

    # clean up your resources so that the column names match on radio_code_df and agg_df
    # we will want to join on the disposition code
    radio_code_df = radio_code_df.withColumnRenamed("disposition_code", "disposition")
    join_query = agg_df.join(radio_code_df, "disposition")

    join_query_writer = join_query \
        .writeStream \
        .queryName("join_radio_code") \
        .outputMode("append") \
        .format("console") \
        .start()

    join_query_writer.awaitTermination()

if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # TODO Create Spark in Standalone mode
    spark = SparkSession \
        .builder \
        .master("local[*]") \
        .appName("KafkaSparkStructuredStreaming") \
        .config("spark.ui.port", 3000) \
        .getOrCreate()

    spark.sparkContext.setLogLevel('WARN')

    logger.info("Spark started")

    run_spark_job(spark)

    spark.stop()
