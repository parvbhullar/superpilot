import numpy as np
import math
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import TruncatedSVD

# Function to retrieve agent responses


# Preprocess personas for text representation
def preprocess_personas(personas):
    return [" ".join([p["persona_name"], " ".join(p["tags"]), p["about"], p["persona"]]) for p in personas]

# 1. TF-IDF Cosine Similarity
def rank_tfidf_cosine(personas, query):
    persona_texts = preprocess_personas(personas)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(persona_texts + [query])
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    ranked_personas = sorted(zip(personas, cosine_sim), key=lambda x: x[1], reverse=True)
    return [p[0]["persona_name"] for p in ranked_personas]

# 2. BM25
def rank_bm25(personas, query):
    k, b = 1.5, 0.75
    persona_texts = preprocess_personas(personas)
    avg_len = np.mean([len(text.split()) for text in persona_texts])
    scores = []
    
    for text in persona_texts:
        score = 0
        words = text.split()
        query_terms = query.split()
        for term in query_terms:
            term_freq = words.count(term)
            doc_len = len(words)
            idf = math.log((len(persona_texts) - sum(term in t for t in persona_texts) + 0.5) / (sum(term in t for t in persona_texts) + 0.5) + 1)
            score += idf * ((term_freq * (k + 1)) / (term_freq + k * (1 - b + b * (doc_len / avg_len))))
        scores.append(score)
    
    ranked_personas = sorted(zip(personas, scores), key=lambda x: x[1], reverse=True)
    return [p[0]["persona_name"] for p in ranked_personas]

# 3. Embedding-Based Cosine Similarity (Sentence-BERT)
def rank_embedding_similarity(personas, query):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    persona_texts = preprocess_personas(personas)
    embeddings = model.encode(persona_texts + [query])
    query_embedding = embeddings[-1]
    cosine_sim = cosine_similarity([query_embedding], embeddings[:-1]).flatten()
    ranked_personas = sorted(zip(personas, cosine_sim), key=lambda x: x[1], reverse=True)
    return [p[0]["persona_name"] for p in ranked_personas]

# 4. Latent Semantic Analysis (LSA)
def rank_lsa(personas, query):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(preprocess_personas(personas) + [query])
    svd = TruncatedSVD(n_components=5)
    lsa_matrix = svd.fit_transform(tfidf_matrix)
    query_vec = lsa_matrix[-1]
    similarities = cosine_similarity([query_vec], lsa_matrix[:-1]).flatten()
    ranked_personas = sorted(zip(personas, similarities), key=lambda x: x[1], reverse=True)
    return [p[0]["persona_name"] for p in ranked_personas]

# 5. Rule-Based Matching (Keyword-Based with Boosted Tags)
def rank_rule_based(personas, query):
    query_terms = set(query.split())
    scores = []
    for p in personas:
        persona_text = " ".join([p["persona_name"], " ".join(p["tags"]), p["about"], p["persona"]])
        score = sum(1.5 if term in p["tags"] else 1 for term in query_terms if term in persona_text)
        scores.append(score)
    ranked_personas = sorted(zip(personas, scores), key=lambda x: x[1], reverse=True)
    return [p[0]["persona_name"] for p in ranked_personas]

# 6. Jaccard Similarity
def rank_jaccard_similarity(personas, query):
    query_set = set(query.lower().split())
    scores = []
    for persona in personas:
        persona_set = set(persona['tags'] + persona['about'].lower().split() + persona['persona'].lower().split())
        intersection = len(query_set.intersection(persona_set))
        union = len(query_set.union(persona_set))
        jaccard_index = intersection / union if union > 0 else 0
        scores.append(jaccard_index)
    
    ranked_personas = sorted(zip(personas, scores), key=lambda x: x[1], reverse=True)
    return [p[0]["persona_name"] for p in ranked_personas]

# Aggregate rankings with statistical basis
def aggregate_rankings(*ranked_lists):
    score_dict = {}
    for ranked_list in ranked_lists:
        for i, persona_name in enumerate(ranked_list):
            score = len(ranked_list) - i
            score_dict[persona_name] = score_dict.get(persona_name, 0) + score
    
    ranked_personas_final = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
    #return [persona for persona, _ in ranked_personas_final]
    return ranked_personas_final

# Final function to rank personas by multiple methods and aggregate
def rank_personas_list(personas,query):
    # personas = generate_agent_response(query)
    personas = [persona for persona in personas if persona["tags"]]

    ranked_personas_tfidf = rank_tfidf_cosine(personas, query)
    ranked_personas_bm25 = rank_bm25(personas, query)
    ranked_personas_embedding = rank_embedding_similarity(personas, query)
    ranked_personas_lsa = rank_lsa(personas, query)
    ranked_personas_rule_based = rank_rule_based(personas, query)
    ranked_personas_jaccard = rank_jaccard_similarity(personas, query)

    final_ranking = aggregate_rankings(
        ranked_personas_tfidf,
        ranked_personas_bm25,
        ranked_personas_embedding,
        ranked_personas_lsa,
        ranked_personas_rule_based,
        ranked_personas_jaccard
    )

    #print("Final Aggregated Ranking:")
    return(final_ranking)

