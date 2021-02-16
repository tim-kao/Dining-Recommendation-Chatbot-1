#!/usr/bin/env python

"""
    Copyright (c) 2013, Triad National Security, LLC
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
    following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
      disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
      following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of Triad National Security, LLC nor the names of its contributors may be used to endorse or
      promote products derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
    INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
    WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
    Example call:
        ./examples.py "[API Key]"
"""
import datetime
import requests
import json
from yelpapi import YelpAPI
import argparse
from pprint import pprint
from elasticsearch import Elasticsearch

API_KEY = 'zbzcbEOTxu4yHssu1-4NqiShil9PZmvIY4ZfpyfClyPq_InXbfzcCSXL3AQkrjdQ17w44ZLJRSZ-vgp8tKYmhFWlk1rxtIPqJdq6BQVOLlK0RBAZH3b8qVGIyu0GYHYx'

yelp_api = YelpAPI(API_KEY)

"""
    Example search by location text and term. 

    Search API: https://www.yelp.com/developers/documentation/v3/business_search
"""
print('***** 5 best rated ice cream places in Austin, TX *****\n{}\n'.format("yelp_api.search_query(term='ice cream', "
                                                                             "location='austin, tx', sort_by='rating', "
                                                                             "limit=5)"))
#tim, Windows2020;
#for _ in range(100/50):

cuisines = ['Caribbean restaurants', 'japanese restaurants', 'italian restaurants', 'italian restaurants', 'chinese restaurants', 'american restaurant']
default_term = 'japanese restaurants'
location = 'manhattan'
search_limit = 50

es = Elasticsearch(
    ['localhost'],
    http_auth=('tim', 'Windows2020;'),
    scheme="http",
    port=9200,
)

# delete
"""
for i in range(60):
    test = es.delete(index='restaurants', id=i)
    print(test['result'])

"""
for cuisine in cuisines:
    for i in range(20, 40):    # populate 5000 results to elasticsearch, Caribbean 0-20, japanese 20-40, italian 40-60, Caribbean
        response = yelp_api.search_query(term=default_term, location=location, sort_by='rating', limit=search_limit, offset=(i % 20) * search_limit)
        json_data = response.json()['businesses']
        test = es.index(index='restaurants', ignore=400, doc_type='docket', id=i, body=json_data)
        print(test['result'])

es.indices.refresh(index="restaurants")
res = es.search(index="restaurants", body={"query": {"match_all": {}}})
print("Got %d Hits:" % res['hits']['total']['value'])
for hit in res['hits']['hits']:
    print(hit)

