#!/usr/bin/env python

from datetime import datetime
import requests
import json
from yelpapi import YelpAPI
import argparse
from pprint import pprint
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import collections
import csv
import boto3
import pandas as pd
from time import sleep

cuisines = ['caribbean', 'japanese', 'italian', 'chinese', 'american', 'mexico', 'korean']
csv_indexes = ['restaurantID', 'cuisine']
columns = csv_indexes + \
          ['name', 'rating', 'phone', 'location', 'is_closed', 'transactions', 'url', 'image_url', 'review_count', 'InsertedAtTimeStamp', 'zip_code', 'coordinates']
locations = ['manhattan']

json_file_name = "es.json"
data_repository = "db.xlsx"
API_KEY = 'zbzcbEOTxu4yHssu1-4NqiShil9PZmvIY4ZfpyfClyPq_InXbfzcCSXL3AQkrjdQ17w44ZLJRSZ-vgp8tKYmhFWlk1rxtIPqJdq6BQVOLlK0RBAZH3b8qVGIyu0GYHYx'
dynamodb_table_name = 'yelp-restaurants'
dynamodb_region = 'us-east-1'
yelp_api = YelpAPI(API_KEY)

#tim, Windows2020;
#cuisines = ['caribbean', 'japanese']
number_of_results_per_cuisine = 1000
search_limit = 50

def fetch_from_Yelp():
    """
    Fetch data from Yelp API and generate data for ES and Dynamodb
    :return: data for elasticsearch and dynamodb
    """
    elastic_rows = []  # a list of dictionaries.
    dynamo_rows = []  # a list of dictionaries.
    for location in locations:
        for cuisine in cuisines:
            for i in range(int(number_of_results_per_cuisine/search_limit)):
                search_term = cuisine + " restaurant"
                response = yelp_api.search_query(term=search_term, location=location, sort_by='rating', limit=search_limit, offset=i * search_limit)
                sleep(0.1)
                for row in response['businesses']:
                    csv_row = {}
                    es_row = {csv_indexes[0]: row['id'], csv_indexes[1]: cuisine}
                    for column in columns:
                        if column == 'InsertedAtTimeStamp':
                            csv_row['InsertedAtTimeStamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        elif column == csv_indexes[0]:
                            csv_row[column] = row['id']
                        elif column == csv_indexes[1]:
                            csv_row[csv_indexes[1]]  = cuisine
                        elif column == 'coordinates':
                            csv_row[column] = str(row['coordinates']['latitude'])+','+str(row['coordinates']['longitude'])
                        elif column == 'rating':
                            csv_row[column] = str(row[column])
                        elif column == 'zip_code':
                            csv_row[column] = row['location']['zip_code']
                        else:
                            csv_row[column] = row[column]
                    elastic_rows.append(es_row)
                    dynamo_rows.append(csv_row)
                print("Fetch cuisine", cuisine, "restaurants data", 100*(i + 1)/20, "% done")

    return elastic_rows, dynamo_rows


def write_to_dynamodb(rows, db=None, table_name=dynamodb_table_name):
    """
    Populate data on dynamodb.
    :param rows: Prepared data from Yelp API, a list of dictionaries.
    :param db: database resource
    :param table_name: Assigned table name
    :return: response from dynamodb
    """
    if not db:
        db = boto3.resource('dynamodb', region_name=dynamodb_region)
    table = db.Table(table_name)
    for i, row in enumerate(rows):
        response = table.put_item(Item=row)
        if i % 100 == 0:
            print("Upload", i, "rows")
    print('Write data to dynamodb, total', len(rows), 'rows')
    return response

def write_to_bulk(filename, rows):
    """
    Populate data to .json with bulk API format for elasticsearch
    :param filename: target file name.
    :param rows: elasticsearch data.
    :return: True o False. True: commit to the file successfully. False: commit fails.
    Example format:
    {"index": {"_index": "restaurants", "_type": "Restaurant", "_id": "0"}}
    {"Restaurant": {"restaurantID": "xxx", "cuisine": "xxx"}}
    generate json bulk format for es
    """
    if rows:
        string1_1 = '{"index": {"_index": "restaurants", "_type": "Restaurant", "_id":"'
        string1_2 = '"}}\n'
        string2_1 = '{"Restaurant": {"restaurantID":"'
        string2_2 = '", "cuisine": "'
        f = open(filename, 'w+')
        for i, row in enumerate(rows):
            string1 = string1_1 + str(i) + string1_2
            string2 = string2_1 + str(row[csv_indexes[0]]) + string2_2 + row[csv_indexes[1]] + string1_2
            f.write(string1)
            f.write(string2)
        f.close()
        return True
    else:
        return False


es_data, db_data = fetch_from_Yelp()
es_res = write_to_bulk(json_file_name, es_data)
if es_res:
    print("es.json is written successfully.")
else:
    print("No available data to generate.")
dynamodb_response = write_to_dynamodb(db_data)
print(dynamodb_response)

