"""Reddit posts/comments about accessibility (lived-experience text).

Posts and comments are separate rows; authors are salted hashes (no usernames stored).
Raw text stays local: release only IDs (Reddit Data API terms).
"""
from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime

import pandas as pd

from ..core import now, out_dir


def _client():
    import praw
    from dotenv import load_dotenv
    load_dotenv()
    return praw.Reddit(client_id=os.environ["REDDIT_CLIENT_ID"],
                       client_secret=os.environ["REDDIT_CLIENT_SECRET"],
                       user_agent=os.environ["REDDIT_USER_AGENT"])


def _doc(thing, kind, parent, sub, query, region, retrieved):
    salt = os.environ["ANON_SALT"]
    return {"doc_id": thing.fullname, "parent_id": parent, "kind": kind, "subreddit": sub, "query": query,
            "created_utc": datetime.fromtimestamp(thing.created_utc, UTC).isoformat(),
            "title": getattr(thing, "title", ""), "text": thing.selftext if kind == "post" else thing.body,
            "score": thing.score,
            "author_hash": hashlib.sha256(f"{salt}:{thing.author}".encode()).hexdigest()[:12],
            "permalink": f"https://www.reddit.com{thing.permalink}", "region": region,
            "retrieved_at": retrieved}


def run(name: str, spec: dict, region: str, limit: int = 100) -> pd.DataFrame:
    reddit, retrieved, kws = _client(), now(), [k.lower() for k in spec["keywords"]]
    jobs = [(s, k) for s in spec["subreddits"][region] for k in spec["keywords"]]
    jobs += [(s, f'"{p}" {k}') for s in spec["global_subreddits"] for p in spec["place_terms"][region]
             for k in ("wheelchair", "accessible")]
    docs, seen = [], set()
    for sub, query in jobs:
        try:
            posts = list(reddit.subreddit(sub).search(query, sort="relevance", limit=limit))
        except Exception as e:  # missing / private subreddit
            print(f"skip r/{sub} {query!r}: {e}")
            continue
        for post in (p for p in posts if p.id not in seen):
            seen.add(post.id)
            docs.append(_doc(post, "post", "", sub, query, region, retrieved))
            post.comments.replace_more(limit=0)
            docs += [_doc(c, "comment", post.fullname, sub, query, region, retrieved)
                     for c in post.comments.list() if any(k in c.body.lower() for k in kws)]
    df = pd.DataFrame(docs)
    df.to_parquet(out_dir(region) / f"{name}.docs.parquet", index=False)  # text corpus, not observations
    return df
