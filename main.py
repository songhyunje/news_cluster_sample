import datetime
import json
import sys
import logging
import random
import pickle
from collections import defaultdict, Counter

from search_handler import Searcher
from wire_handler import Wire
from utils import jaccard_similarity 
import clustering


searcher = Searcher()
wire = Wire()
logger = logging.getLogger(__name__)


def get_news(keyword, from_date, to_date, category, publisher):
    logger.debug(f'keyword: {keyword}, from_date: {from_date}, to_date: {to_date}, category: {category}, publisher: {publisher}')
    fields = ['newsTitle', 'extContent', 'imageUrl', 'caption', 'originalUrl', 'postingDate']

    news = []
    for hit in searcher.search(query=keyword, from_date=from_date, to_date=to_date, 
                               category=category, publisher=publisher, fields=fields):
        news.extend([(hit.newsTitle, hit.extContent, hit.imageUrl, hit.caption, hit.originalUrl)])

    return news


def cluster(news):
    _, contents, _, _, _ = zip(*news)
    # Get embeddings
    embeddings = wire.get_embeddings(contents)
    # clustering
    labels = clustering.dense_clustering(embeddings)
    # labels = clustering.clustering(contents, min_news)
    return labels


def summarize(source, date):
    sds_output = wire.sds(source, date=date)
    summary = sds_output.get("summ_result", "")
    first_sent = wire.get_first_sentence(source)
    return summary, first_sent


if __name__ == '__main__':
    keyword = "올림픽"
    from_date = "2022-01-25"
    to_date = "2022-02-05"
    category = ['금융', '증권', '산업/재계', '중기/벤처', '부동산', '글로벌경제', '생활경제', '경제일반']
    publisher = ['enews24', 'JTBC', 'KBS', 'MBC', 'MBN', 'SBS', 'YTN', '경향신문', '국민일보', '노컷뉴스', 
                 '뉴시스', '동아일보', '마이데일리', '매경이코노미', '매일경제', '머니S', '머니투데이', '서울경제', 
                 '세계일보', '아시아경제', '연합뉴스', '이데일리', '전자신문', '조선비즈', '조선일보', '중앙일보', 
                 '한겨레', '한경비즈니스', '한국경제', '한국경제TV', '한국일보', '헤럴드경제']

    news = get_news(keyword, from_date, to_date, category, publisher)
    labels = cluster(news)

    cluster = defaultdict(list)
    for idx, news_info in zip(labels, news):
        if idx == -1:
            continue
        cluster[idx].append(news_info) 

    summaries = []
    for idx in sorted(cluster, key=lambda x:len(cluster[x]), reverse=True):
        logger.debug(f'cluster idx: {idx}, len: {len(cluster[idx])}')
        # if len(summaries) > 5 or len(cluster[idx]) < 10:
        #     continue

        # titles, contents, image_urls, captions, news_urls
        _, contents, _, _, news_urls = zip(*cluster[idx])
        summary, first_sent = summarize(contents[0], to_date)
        print(f'요약:{summary}\n첫문장:{first_sent}\nurls:{news_urls}\n\n')


