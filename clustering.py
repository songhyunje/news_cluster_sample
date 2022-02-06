from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer

import random
import hdbscan
import umap
# import mecab
# 
# 
# mecab = mecab.MeCab()
# 
# 
# def clustering(docs, min_cluster=5, min_df=3):
#     vectorizer = TfidfVectorizer(max_df=0.8, max_features=10000, min_df=min_df,
#                                  tokenizer=mecab.morphs, use_idf=True)
#     X = vectorizer.fit_transform(docs)
#     model = hdbscan.HDBSCAN(min_cluster_size=min_cluster, 
#                             cluster_selection_method='eom').fit(X)
#     return model.labels_


def dense_clustering(embeddings, min_cluster=3):
    umap_embeddings = umap.UMAP(n_neighbors=15, 
                                n_components=5, 
                                metric='cosine').fit_transform(embeddings)
    cluster = hdbscan.HDBSCAN(min_cluster_size=min_cluster, 
                              metric='euclidean', 
                              cluster_selection_method='eom').fit(umap_embeddings)
    return cluster.labels_

