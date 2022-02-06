import logging
import json
import copy
from collections import defaultdict

import numpy as np
import requests
import yaml

from kss import split_sentences


LOG_FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, 'INFO'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

headers = {'Content-Type': 'application/json'}


class Wire(object):
    def __init__(self, config="config.yaml"):
        with open(config, 'r') as yaml_fn:
            cfg = yaml.load(yaml_fn, Loader=yaml.BaseLoader)

        self.summarizer_url = cfg['summarizer']['url']
        self.mds_url = cfg['multi_summarizer']['url']
        self.image_url = cfg['image_selector']['url']
        self.factcc_url = cfg['fact_corrector']['url']

        self.embedding_url = cfg['embedding_model']['url']
        self.timeline_url = cfg['timeline']['url']

    @staticmethod
    def call_api(url, data, timeout=5, verbose=True):
        logger.info(url)
        if verbose:
            logger.info(json.dumps(data, ensure_ascii=False))
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
        except:
            return {}

        return {}

    def sds(self, text, date): 
        inputs = {"src_id": 1, "date": date, "src": text}
        outputs = self.call_api(self.summarizer_url, inputs)
        return outputs

    def mds(self, docs):
        inputs = {}
        if isinstance(docs, list):
            inputs["corpus"] = docs
        else:
            return {}

        outputs = self.call_api(self.mds_url, inputs)
        # inputs = {"src_id": 1, "date":"", "src": text}
        # outputs = self.call_api(self.summarizer_url, inputs)
        # summ_result, src_id, date, time_spend
        # outputs = None

        return outputs

    def factcc(self, src, summary): 
        inputs = {"src_id": 1, "src": src, "summary": summary}
        outputs = self.call_api(self.factcc_url, inputs)
        return outputs

    def pre_analyzed_topics_url(self):
        outputs = self.call_api(self.topic_model)
        logger.info(outputs)
        return outputs

    def pre_analyzed_topics(self):
        raw_topics = self.topic_model.get_topics()
        topics = []
        for topic in raw_topics:
            if topic == -1:
                continue

            topic_id = f"tid{topic}"
            topic_name = f"topic{topic}"

            topic_words = []
            for v in raw_topics[topic][:30]:
                token = ''.join(v[0].split())
                if token.startswith('##') or token.startswith('.'):
                    continue

                token = token.replace('##', '')
                topic_words.append(token)
                
                if len(topic_words) > 10:
                    break
            # topic_words = [v[0] for v in raw_topics[topic][:30]]

            topics.append({"id": topic_id, "name": topic_name, "words": topic_words})

        return topics

    def get_topic_words_url(self, tid, num=30):
        logger.info(f'tid: {tid}') 
        topics = self.pre_analyzed_topics_url()
        tid = int(tid[3:])

        topic_words = []
        for v in topics[tid][:num]:
            token = ''.join(v[0].split())
            if token.startswith('##') or token.startswith('.'):
                continue

            token = token.replace('##', '')
            topic_words.append(token)
        
        return topic_words 

    def get_topic_words(self, tid, num=30):
        logger.info(f'tid: {tid}') 
        topics = self.topic_model.get_topics()
        tid = int(tid[3:])

        topic_words = []
        for v in topics[tid][:num]:
            token = ''.join(v[0].split())
            if token.startswith('##') or token.startswith('.'):
                continue

            token = token.replace('##', '')
            topic_words.append(token)
        
        return topic_words 

    def get_first_sentence(self, doc):
        return split_sentences(doc, backend="none")[0]

    def get_embeddings(self, docs):
        outputs = [] 
        for x in range(0, len(docs), 500):
            inputs = {"docs": docs[x:x+500]}
            results = self.call_api(self.embedding_url, inputs, timeout=10, verbose=False)
            outputs.extend(results['embeddings'])

        return np.asarray(outputs)

    def topic_inference(self, docs):
        embeddings = self.get_embeddings(docs)
        topics, probs = self.topic_model.transform(docs, embeddings)
        return topics, probs

    def timeline(self, counter, threshold=0.5, min_dist=1):
        inputs = {"counter": counter, 'threshold': threshold, 'min_dist': min_dist}
        outputs = self.call_api(self.timeline_url, inputs)
        logger.info(outputs)
        return outputs

    def image_selector(self, text, images):
        inputs = {}
        if text and images:
            image_caption = [{'url': url, 'caption': caption, 'title': title, 'firstsen': firstsent} 
                              for url, caption, title, firstsent in images]
            inputs["text_query"] = text
            inputs["image_texts"] = image_caption

        outputs = self.call_api(self.image_url, inputs, timeout=20)
        return outputs 

