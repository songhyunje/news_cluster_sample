import logging
from datetime import datetime, timedelta

import yaml
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, UpdateByQuery, Q


logging.basicConfig(level=getattr(logging, 'INFO'))
logger = logging.getLogger(__name__)


class Searcher(object):
    def __init__(self, hosts=None, news_index=None, http_auth=None):
        with open("config.yaml", 'r') as yaml_fn:
            cfg = yaml.load(yaml_fn, Loader=yaml.BaseLoader)

        hosts = cfg['elasticsearch']['hosts'] if hosts is None else hosts
        http_auth = cfg['elasticsearch']['http_auth'] if http_auth is None else http_auth
        news_index = cfg['elasticsearch']['news_index'] if news_index is None else news_index

        self.client = Elasticsearch(hosts=hosts)
        self.news_index = news_index
        self.client = Elasticsearch(
            hosts=hosts,
            http_auth=http_auth,
            scheme='https',
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False,
            timeout=30)

    @staticmethod
    def _covert_to_datetime(from_datetime, to_datetime):
        if not to_datetime:
            to_datetime = datetime.now()
        if not from_datetime:
            from_datetime = to_datetime - timedelta(days=1)

        if not isinstance(from_datetime, datetime):
            from_datetime = datetime.strptime(from_datetime, '%Y-%m-%d')

        if not isinstance(to_datetime, datetime):
            to_datetime = datetime.strptime(to_datetime, '%Y-%m-%d')

        to_datetime = to_datetime.strftime("%Y-%m-%d")
        from_datetime = from_datetime.strftime("%Y-%m-%d")

        return from_datetime, to_datetime

    def search(self, query=None, from_date=None, to_date=None, 
               publisher=[], category=[], fields=[], op='AND'):
        from_datetime, to_datetime = self._covert_to_datetime(from_date, to_date)
        should = []
        if isinstance(publisher, list):
            should.extend([Q('match', companyName=p) for p in publisher])
        else:
            should.append(Q('match', companyName=publisher))

        if isinstance(category, list):
            should.extend([Q('match', category=c) for c in category])
        elif category:
            should.append(Q('match', category=category))

        if isinstance(fields, str):
            fields = [fields]

        if query:
            if op == 'AND':
                must = [Q("match", extContent=query_token) for query_token in query.split()]
            else:
                must = [Q("match", extContent=query)]
            # q = Q('bool', must=must, should=should)
            if category and publisher:
                q = Q('bool', must=must, should=should, minimum_should_match=2)
            else:
                q = Q('bool', must=must, should=should)
        else:
            # q = Q('bool', should=should)
            q = Q('bool', should=should, minimum_should_match=2)

        # q = Q('bool', should=should)
        # if query:
        #     q &= Q('bool', must=[Q("match", extContent=query)])

        s = Search(using=self.client, index=self.news_index) \
            .source(fields) \
            .query(q) \
            .filter('range', postingDate={'from': from_datetime, 'to': to_datetime})

        for hit in s.scan():
            yield hit

    def search_specific_date(self, query=None, date=None, fields=[]):
        if not isinstance(date, datetime):
            from_datetime = datetime.strptime(date, '%Y-%m-%d')

        to_datetime = from_datetime + timedelta(days=1)

        from_datetime = from_datetime.strftime("%Y-%m-%d")
        to_datetime = to_datetime.strftime("%Y-%m-%d")

        return self.search(query, from_datetime, to_datetime, fields=fields)

    def search_for_collector_paginate(self, query=None, from_date=None, to_date=None, fields=[],
                                      publisher=[], category=[], page_num=1, size=500, op='AND'):
        should = []
        if isinstance(publisher, list):
            should.extend([Q('match', companyName=p) for p in publisher])
        else:
            should.append(Q('match', companyName=publisher))

        if isinstance(category, list):
            should.extend([Q('match', category=c) for c in category])
        else:
            should.append(Q('match', category=category))

        if isinstance(fields, str):
            fields = [fields]

        # # publisher / category
        # q = Q('bool', should=should, minimum_should_match=2)
        #     q &= Q("match", extContent=query)

        if query:
            if op == 'AND':
                must = [Q("match", extContent=query_token) for query_token in query.split()]
            else:
                must = [Q("match", extContent=query)]

            # must = [Q("match", extContent=query_token) for query_token in query.split()]
            q = Q('bool', must=must, should=should, minimum_should_match=2)
        else:
            q = Q('bool', should=should, minimum_should_match=2)

        s = Search(using=self.client, index=self.news_index) \
            .source(fields) \
            .query(q) \
            .filter('range', postingDate={'from': from_date, 'to': to_date})

        return s.count(), s[size*(page_num-1):size*page_num].execute()


    def search_by_newsid(self, news_ids, fields=[]):
        if isinstance(fields, str):
            fields = [fields]

        should = []
        if isinstance(news_ids, (list, set)):
            should.extend([Q('match', _id=t) for t in news_ids])
        else:
            should.append(Q('match', _id=news_ids))

        q = Q('bool', should=should)
        s = Search(using=self.client, index=self.news_index) \
            .source(fields) \
            .query(q)

        for hit in s.scan():
            yield hit


    def search_by_date(self, from_date, to_date, fields=[]):
        return self.search(query=None, from_date=from_date, to_date=to_date, fields=fields)


