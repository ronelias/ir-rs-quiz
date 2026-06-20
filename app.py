"""
IR & RS Quiz — Kahoot-style live quiz
Host URL : <your-app-url>?host=true
Player URL: <your-app-url>
"""
import streamlit as st
import sqlite3
import time
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
QUESTION_TIME = 30
HOST_PASSWORD = "prof2026"
POLL_INTERVAL = 1.5
DB_PATH       = Path("quiz.db")

COLORS = ["#e21b3c", "#1368ce", "#d89e00", "#26890c"]
SHAPES = ["▲", "◆", "●", "✕"]

# ── QUESTIONS ─────────────────────────────────────────────────────────────────
# (question_text, [answer1..4], correct_1_based, explanation)
QUESTIONS = [

    # ── L1: IR Introduction ───────────────────────────────────────────────────
    ("Which of the following best describes unstructured data?",
     ["Data stored in relational database tables",
      "Free text documents like emails and web pages",
      "XML files with defined schemas",
      "Spreadsheets with labeled columns"], 2,
     "Unstructured data lacks a predefined schema. Free text — emails, web pages, PDFs — is the classic example, unlike relational tables which enforce a rigid structure."),

    ("What is the main goal of an Information Retrieval system?",
     ["To store data efficiently in a database",
      "To encrypt sensitive documents",
      "To find material satisfying an information need from a large collection",
      "To compress large document collections"], 3,
     "IR systems retrieve relevant documents from large unstructured collections based on a user's information need — they are not storage, encryption, or compression systems."),

    ("An IR system is formally defined by three components. Which answer correctly lists them?",
     ["Crawler, parser, and compressor",
      "Tokenizer, stemmer, and stop-word list",
      "Representation of queries, documents, and a ranking/relevance function",
      "Database schema, query optimizer, and result cache"], 3,
     "The formal definition requires: (1) a representation for documents, (2) a representation for queries, and (3) a comparison function that ranks results by relevance."),

    # ── L2: Boolean Model ─────────────────────────────────────────────────────
    ("In the fuzzy/extended Boolean model, how are term weights typically represented?",
     ["As integers (0, 1, 2, 3...)",
      "As real-valued scores between 0 and 1",
      "As binary bit strings",
      "As negative values for irrelevant terms"], 2,
     "The extended Boolean model moves beyond binary presence (0/1) to allow terms to have partial membership expressed as real-valued weights in [0,1], enabling graded relevance."),

    # ── L3: Vector Space Model ────────────────────────────────────────────────
    ("In the Vector Space Model, documents and queries are represented as:",
     ["Binary bit vectors",
      "Relational tables",
      "Weighted term vectors in a high-dimensional space",
      "Linked lists of tokens"], 3,
     "In VSM, each unique term is one dimension. Documents and queries become vectors where each component is a term weight (e.g., TF-IDF), enabling geometric similarity comparisons."),

    ("The IDF (Inverse Document Frequency) of a term is HIGH when:",
     ["The term appears in many documents",
      "The term appears in very few documents",
      "The term has high within-document frequency",
      "The term is a stop word"], 2,
     "IDF = log(N/df). When a term appears in few documents (low df), N/df is large, giving high IDF. Rare terms are more discriminative and receive higher weights."),

    ("Cosine similarity between two document vectors is computed as:",
     ["The dot product of raw term frequencies",
      "The Euclidean distance between vectors",
      "Dot product of normalized vectors divided by product of their magnitudes",
      "Sum of absolute differences between vector components"], 3,
     "cos(θ) = (A·B)/(|A|×|B|). Dividing by magnitudes normalizes for document length, so a short and a long document covering the same topic will score similarly."),

    ("Why do we normalize document vectors by their length in cosine similarity?",
     ["To make all term weights positive",
      "To remove stop words from the computation",
      "To neutralize the effect of document length on similarity",
      "To increase the speed of index lookup"], 3,
     "Without length normalization, longer documents have higher raw frequencies and score higher simply due to size. Division by the vector magnitude removes this length bias."),

    # ── L4: Text Operations ───────────────────────────────────────────────────
    ("Tokenization is the process of:",
     ["Ranking documents by relevance score",
      "Breaking a text stream into individual terms/tokens",
      "Removing duplicate documents from a collection",
      "Compressing index files"], 2,
     "Tokenization is the first text-processing step: splitting raw text into individual units (tokens). Choices include handling punctuation, hyphens, numbers, and whitespace."),

    ("Zipf's Law states that:",
     ["Term frequency grows logarithmically with collection size",
      "The product of a term's rank and its frequency is approximately constant",
      "Rare words carry more meaning than common words",
      "Most documents contain fewer than 100 unique terms"], 2,
     "Zipf: rank × frequency ≈ constant. The most frequent word appears ~2× as often as the 2nd most frequent, 3× the 3rd, etc. This motivates stop-word removal for the top terms."),

    ("The Porter Stemming algorithm works by:",
     ["Looking up words in a dictionary of canonical forms",
      "Applying a series of suffix-stripping rules",
      "Using machine learning to predict word roots",
      "Replacing all words with their phonetic codes"], 2,
     "Porter stemmer applies ordered hand-crafted rules to strip common English suffixes (e.g., 'running'→'run', 'happiness'→'happi'). It is fast but not always linguistically accurate."),

    ("In the Noisy Channel model, the system selects the correction that maximizes:",
     ["Edit distance to the original word",
      "Term frequency in the index",
      "P(word) x P(observed|word) - prior times channel probability",
      "The number of vowels in the candidate word"], 3,
     "The Noisy Channel treats the misspelling as a word sent through noise. The best correction maximizes P(word)×P(error|word) — combining a language-model prior with the channel noise probability."),

    ("Edit distance (Levenshtein) counts the minimum number of:",
     ["Characters in the longer word",
      "Insertions, deletions, and substitutions to transform one string to another",
      "Shared substrings between two words",
      "Vowel differences between two words"], 2,
     "Levenshtein distance is computed with dynamic programming and counts the minimum insert, delete, or substitute operations needed to turn one string into another. Used for spell-correction candidate generation."),

    # ── L5: Indexing ──────────────────────────────────────────────────────────
    ("The three steps for constructing an inverted index - what does each step do?",
     ["Crawl (fetch pages) -> Compress (shrink) -> Query (answer requests)",
      "Tokenize -> Sort (order term-docID pairs) -> Group/merge (posting lists)",
      "Parse (read docs) -> Rank (score by TF-IDF) -> Store (write to disk)",
      "Stem (normalize) -> Weight (TF-IDF) -> Cluster (group similar docs)"], 2,
     "Index construction: (1) Tokenize documents into (term, docID) pairs; (2) Sort all pairs alphabetically by term; (3) Merge consecutive entries for the same term into a posting list."),

    ("A positional index stores, for each term:",
     ["Only the list of documents containing that term",
      "Document IDs and positions of each occurrence within each document",
      "The TF-IDF weight of the term per document",
      "The number of documents in which the term appears"], 2,
     "A positional index extends the basic inverted index by storing the exact word-offset of each term in each document, enabling phrase queries (e.g., 'New York') by checking adjacent positions."),

    ("Heaps' Law describes the relationship between:",
     ["Term frequency and document frequency",
      "Collection size and vocabulary size - vocabulary grows sub-linearly",
      "Index size and query response time",
      "Number of documents and average document length"], 2,
     "Heaps' Law: V ≈ k·Tᵝ (β ≈ 0.5). As a collection grows, new unique words keep appearing but at a decreasing rate — sub-linear growth, useful for estimating index size."),

    ("In BSBI (Block Sort-Based Indexing), blocks are processed because:",
     ["The full collection fits easily in RAM",
      "Collection does not fit in RAM; each block is sorted then merged",
      "MapReduce requires fixed-size input blocks",
      "Positional indexes must be built incrementally"], 2,
     "BSBI splits the collection into RAM-sized blocks, sorts each block individually, then merges them via k-way merge — enabling index construction for collections larger than available memory."),

    ("A biword index stores:",
     ["Single terms only",
      "Consecutive pairs of terms as index entries",
      "All n-grams up to length 5",
      "Character-level bigrams for fuzzy matching"], 2,
     "A biword index indexes every consecutive word pair (e.g., 'machine learning') as a single token, enabling fast phrase-query matching for two-word phrases without a full positional index."),

    # ── L6: IR Evaluation ─────────────────────────────────────────────────────
    ("Precision is defined as:",
     ["Relevant retrieved / Total relevant in collection",
      "Relevant retrieved / Total retrieved",
      "Total retrieved / Collection size",
      "Relevant in collection / Collection size"], 2,
     "Precision = |Relevant ∩ Retrieved| / |Retrieved|. It measures what fraction of returned results are actually relevant — a high-precision system avoids returning irrelevant documents."),

    ("Recall is defined as:",
     ["Relevant retrieved / Total retrieved",
      "Relevant retrieved / Total relevant documents in collection",
      "Total documents in collection / Relevant retrieved",
      "Precision x F-measure"], 2,
     "Recall = |Relevant ∩ Retrieved| / |Relevant|. It measures what fraction of all relevant documents were found. There is typically a precision-recall tradeoff as the cutoff rank changes."),

    ("Mean Average Precision (MAP) is computed by:",
     ["Averaging precision at a fixed cutoff (P@10) across queries",
      "Computing precision only for the top-ranked document",
      "Averaging the Average Precision scores across all queries",
      "Taking the harmonic mean of precision and recall"], 3,
     "AP for one query is the mean precision at each rank where a relevant document appears. MAP averages AP over all queries, capturing both precision and recall across the full ranked list."),

    ("In DCG, relevance at lower ranks is discounted by:",
     ["Subtracting the rank number from the gain",
      "Dividing the gain by the logarithm of the rank position",
      "Multiplying the gain by (1/rank squared)",
      "Ignoring all results below rank 10"], 2,
     "DCG = Σ rel_i / log₂(i+1). The log discount models the diminishing value of finding a relevant document at rank 5 vs. rank 1 — higher ranks contribute much more to the total."),

    ("Mean Reciprocal Rank (MRR) is most appropriate when:",
     ["All returned documents are equally relevant",
      "You care about the rank of the first relevant document",
      "The collection has no relevant documents",
      "You need to evaluate multi-label ranked lists"], 2,
     "MRR = mean of (1/rank_first_relevant) across queries. Ideal for navigational queries or QA tasks where the user just needs the first correct answer and doesn't care about the rest."),

    ("Inter-annotator agreement in relevance judgments is typically measured using:",
     ["F-measure",
      "Cohen's Kappa",
      "NDCG",
      "MAP"], 2,
     "Cohen's Kappa measures agreement between two annotators while correcting for chance. In IR evaluation, Kappa quantifies how consistently different judges label documents as relevant or not."),

    # ── L7: RS Introduction ───────────────────────────────────────────────────
    ("Which type of filtering recommends items based on the preferences of similar users?",
     ["Content-based filtering",
      "Collaborative filtering",
      "Knowledge-based filtering",
      "Demographic filtering"], 2,
     "Collaborative filtering identifies users with similar tastes (neighbours) and recommends items they liked. It requires no item content features — only the interaction matrix (ratings, clicks, purchases)."),

    ("Content-based filtering recommends items by:",
     ["Finding users with similar rating histories",
      "Analyzing item features and matching them to the user's past preferences",
      "Using explicit rules from domain experts",
      "Randomly sampling popular items"], 2,
     "Content-based filtering builds a user preference profile from past interactions, then recommends new items with similar features. It doesn't need other users' data but can over-specialize."),

    ("A major advantage of hybrid recommender systems is:",
     ["They are always faster than pure approaches",
      "They combine multiple paradigms to overcome individual weaknesses",
      "They require no user data",
      "They only work for movie recommendations"], 2,
     "Hybrid systems combine collaborative and content-based (and knowledge-based) methods to mitigate cold-start, sparsity, and over-specialization problems that individual approaches suffer from."),

    ("The cold start problem in recommender systems occurs when:",
     ["The server runs out of memory during recommendation",
      "A new user or item has little or no interaction history",
      "The recommendation algorithm converges too slowly",
      "The item catalog is too large to process"], 2,
     "Without interaction history for a new user or item, collaborative filtering can't find similar users or compute item similarities. Often addressed with content-based or demographic methods."),

    # ── L8: Collaborative Filtering ───────────────────────────────────────────
    ("In user-based k-NN CF, similarity between users is most commonly measured with:",
     ["Cosine similarity on raw ratings",
      "Euclidean distance on item features",
      "Pearson correlation on co-rated items",
      "Jaccard index on purchased items"], 3,
     "Pearson correlation measures the linear relationship between two users' ratings on co-rated items, accounting for individual bias (e.g., one user always rates high) better than raw cosine similarity."),

    ("The Pearson correlation between users u and v is +1 when:",
     ["They rated exactly the same items",
      "Their ratings are perfectly linearly related (same relative pattern)",
      "They both rated all items with 5 stars",
      "Their average ratings are identical"], 2,
     "Pearson r = +1 when one user's ratings are a positive linear transformation of the other's — same relative ranking even if absolute scales differ (e.g., one rates 3,4,5 and the other rates 1,2,3)."),

    ("Item-based CF predicts a rating using:",
     ["The user's average rating only",
      "Ratings given by the same user to similar items",
      "The global average item rating",
      "The popularity rank of each item"], 2,
     "Item-based CF computes item-item similarity from the rating matrix, then predicts as a weighted average of the user's ratings for the most similar items — more stable over time than user-based CF."),

    ("Slope One predicts a rating by:",
     ["Using matrix factorization of the rating matrix",
      "Learning user and item bias terms with gradient descent",
      "Computing weighted average deviations between co-rated item pairs",
      "Applying association rules from frequent itemsets"], 3,
     "Slope One stores the average rating difference between item pairs across co-raters. Prediction = user's known rating for a related item adjusted by this stored deviation — simple and efficient."),

    ("In SVD-based matrix factorization, the rating matrix R is approximated as:",
     ["R = U x I where U and I are binary matrices",
      "R = P x Q^T where P and Q are low-rank latent factor matrices",
      "R = the average of user and item mean ratings",
      "R = a diagonal matrix of singular values only"], 2,
     "Matrix factorization decomposes R ≈ P·Qᵀ where P (users×k) and Q (items×k) embed users and items in a shared latent space. Missing ratings are predicted from their factor vector dot products."),

    ("An association rule A->B in recommender systems means:",
     ["Buying A causes the user to buy B",
      "Users who liked A tend to also like B with measurable support/confidence",
      "Item A is always more popular than item B",
      "A and B share the same content features"], 2,
     "Association rule A→B means users who interacted with A often also interacted with B. Support measures how common {A,B} is overall; confidence measures P(B|A) — the rule's conditional strength."),

    ("High support for a rule {A, B} means:",
     ["Users rate both A and B with 5 stars",
      "A large proportion of users have interacted with both A and B",
      "The rule has high precision",
      "A predicts B with 100% confidence"], 2,
     "Support({A,B}) = |users who rated both A and B| / |total users|. High support means the co-occurrence is frequent — low-support rules may be statistically spurious and unreliable."),
]

# ── DATABASE ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS state (
            id      INTEGER PRIMARY KEY CHECK(id=1),
            phase   TEXT    NOT NULL DEFAULT 'lobby',
            q_idx   INTEGER NOT NULL DEFAULT 0,
            q_start REAL    NOT NULL DEFAULT 0
        );
        INSERT OR IGNORE INTO state (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS players (
            name   TEXT    PRIMARY KEY,
            score  INTEGER NOT NULL DEFAULT 0,
            joined REAL    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS answers (
            player  TEXT    NOT NULL,
            q_idx   INTEGER NOT NULL,
            choice  INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            pts     INTEGER NOT NULL DEFAULT 0,
            ts      REAL    NOT NULL,
            PRIMARY KEY (player, q_idx)
        );
    """)
    conn.commit()
    return conn


def get_state(conn):
    return dict(conn.execute("SELECT * FROM state WHERE id=1").fetchone())

def set_phase(conn, phase, q_idx=None, q_start=None):
    s = get_state(conn)
    conn.execute(
        "UPDATE state SET phase=?,q_idx=?,q_start=? WHERE id=1",
        (phase,
         s["q_idx"]   if q_idx   is None else q_idx,
         s["q_start"] if q_start is None else q_start)
    )
    conn.commit()

def get_players(conn):
    return conn.execute(
        "SELECT * FROM players ORDER BY score DESC, joined ASC"
    ).fetchall()

def join_game(conn, name):
    try:
        conn.execute("INSERT INTO players VALUES (?,0,?)", (name, time.time()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def submit_answer(conn, player, q_idx, choice, correct, pts):
    try:
        conn.execute(
            "INSERT INTO answers VALUES (?,?,?,?,?,?)",
            (player, q_idx, choice, int(correct), pts, time.time())
        )
        conn.execute("UPDATE players SET score=score+? WHERE name=?", (pts, player))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def has_answered(conn, player, q_idx):
    return conn.execute(
        "SELECT 1 FROM answers WHERE player=? AND q_idx=?", (player, q_idx)
    ).fetchone() is not None

def q_answers(conn, q_idx):
    return conn.execute("SELECT * FROM answers WHERE q_idx=?", (q_idx,)).fetchall()

def reset_game(conn):
    conn.executescript("""
        DELETE FROM players;
        DELETE FROM answers;
        UPDATE state SET phase='lobby', q_idx=0, q_start=0 WHERE id=1;
    """)
    conn.commit()

def calc_pts(remaining):
    return int(500 + 500 * max(0.0, remaining / QUESTION_TIME))


# ── SHARED RENDERING HELPERS ──────────────────────────────────────────────────
def render_timer(remaining):
    """Large coloured countdown + animated progress bar."""
    pct = remaining / QUESTION_TIME
    if pct > 0.5:
        color = "#26890c"
    elif pct > 0.25:
        color = "#d89e00"
    else:
        color = "#e21b3c"
    bar_w = int(pct * 100)
    st.markdown(
        f'<div class="timer-num" style="color:{color}">{int(remaining)}</div>'
        f'<div class="timer-track">'
        f'<div class="timer-fill" style="width:{bar_w}%;background:{color}"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_distribution(all_ans, opts, correct):
    """Coloured horizontal bars showing answer distribution after reveal."""
    total  = max(len(all_ans), 1)
    counts = {i: 0 for i in range(1, 5)}
    for a in all_ans:
        counts[a["choice"]] = counts.get(a["choice"], 0) + 1

    st.markdown("<br>**Answer distribution:**", unsafe_allow_html=True)
    for i, (opt, color, shape) in enumerate(zip(opts, COLORS, SHAPES)):
        n        = counts.get(i + 1, 0)
        pct      = int(n / total * 100)
        is_right = (i + 1) == correct
        border   = "border:2px solid white;" if is_right else ""
        check    = " ✅" if is_right else ""
        width    = max(pct, 4)
        st.markdown(
            f'<div class="dist-bar-wrap">'
            f'<div class="dist-bar" style="background:{color};width:{width}%;{border}">'
            f'{shape} {opt[:42]}{check} &nbsp;({n})'
            f'</div></div>',
            unsafe_allow_html=True,
        )


def render_explanation(explanation):
    """Blue-bordered callout with the answer explanation."""
    st.markdown(
        f'<div class="explanation">💡 {explanation}</div>',
        unsafe_allow_html=True,
    )


def render_leaderboard(players, highlight_name=None, max_rows=10):
    """Styled leaderboard rows, optional player row highlight."""
    medals = ["🥇", "🥈", "🥉"]
    golds  = ["#b8860b", "#707070", "#7a4e2d"]
    for i, p in enumerate(players[:max_rows]):
        m   = medals[i] if i < 3 else f"{i + 1}."
        bg  = golds[i]  if i < 3 else "#2a2a4a"
        me  = " lb-me" if p["name"] == highlight_name else ""
        st.markdown(
            f'<div class="lb{me}" style="background:{bg}">'
            f'{m} {p["name"]} — {p["score"]} pts</div>',
            unsafe_allow_html=True,
        )


def render_podium(players):
    """Top-3 podium block for the end screen."""
    if len(players) < 1:
        return
    order = []
    if len(players) >= 2:
        order = [players[1], players[0]] + ([players[2]] if len(players) >= 3 else [])
    else:
        order = [players[0]]
    heights  = ["130px", "170px", "100px"]
    medals   = ["🥈", "🥇", "🥉"]
    bg_cols  = ["#707070", "#b8860b", "#7a4e2d"]
    html = '<div class="podium">'
    for idx, p in enumerate(order):
        h  = heights[idx]
        m  = medals[idx]
        bg = bg_cols[idx]
        html += (
            f'<div class="podium-block" style="background:{bg};height:{h}">'
            f'<div style="font-size:2rem">{m}</div>'
            f'<div style="font-size:1rem;margin-top:6px">{p["name"]}</div>'
            f'<div style="font-size:0.85rem;opacity:0.9">{p["score"]} pts</div>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── STYLING ───────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');

    /* ── Global typography ── */
    html, body, [class*="css"], h1, h2, h3, p, div, button, input {
        font-family: 'Nunito', sans-serif !important;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }

    /* ── Question box ── */
    .q-box {
        background: #1e1e4a;
        color: white;
        padding: 28px 32px;
        border-radius: 14px;
        font-size: 1.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 20px;
        line-height: 1.4;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }

    /* ── Question badge ── */
    .q-badge {
        display: inline-block;
        background: #1368ce;
        color: white;
        border-radius: 20px;
        padding: 3px 16px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }

    /* ── Timer ── */
    .timer-num {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        line-height: 1;
        margin-bottom: 8px;
        transition: color 0.5s;
    }
    .timer-track {
        height: 14px;
        background: #333360;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 18px;
    }
    .timer-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 1s linear, background 0.5s;
    }

    /* ── Answer buttons — colour by column position ── */
    div[data-testid="column"]:nth-of-type(1) button {
        background: #e21b3c !important;
        color: white !important;
        min-height: 100px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        white-space: normal !important;
        word-wrap: break-word;
        letter-spacing: 0.3px;
        border: none !important;
        box-shadow: 0 4px 12px rgba(226,27,60,0.4) !important;
    }
    div[data-testid="column"]:nth-of-type(2) button {
        background: #1368ce !important;
        color: white !important;
        min-height: 100px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        white-space: normal !important;
        word-wrap: break-word;
        letter-spacing: 0.3px;
        border: none !important;
        box-shadow: 0 4px 12px rgba(19,104,206,0.4) !important;
    }
    div[data-testid="column"]:nth-of-type(3) button {
        background: #d89e00 !important;
        color: white !important;
        min-height: 100px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        white-space: normal !important;
        word-wrap: break-word;
        letter-spacing: 0.3px;
        border: none !important;
        box-shadow: 0 4px 12px rgba(216,158,0,0.4) !important;
    }
    div[data-testid="column"]:nth-of-type(4) button {
        background: #26890c !important;
        color: white !important;
        min-height: 100px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        white-space: normal !important;
        word-wrap: break-word;
        letter-spacing: 0.3px;
        border: none !important;
        box-shadow: 0 4px 12px rgba(38,137,12,0.4) !important;
    }

    /* ── Locked-in card ── */
    .locked-card {
        background: rgba(38,137,12,0.15);
        border: 2px solid #26890c;
        border-radius: 14px;
        padding: 40px 20px;
        text-align: center;
        color: #7ef07e;
        font-size: 1.5rem;
        font-weight: 800;
        margin-top: 20px;
        box-shadow: 0 0 30px rgba(38,137,12,0.2);
    }

    /* ── Explanation callout ── */
    .explanation {
        border-left: 4px solid #1368ce;
        background: rgba(19,104,206,0.12);
        color: #c0d8ff;
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        margin-top: 16px;
        margin-bottom: 8px;
        font-size: 0.98rem;
        line-height: 1.6;
    }

    /* ── Distribution bars ── */
    .dist-bar-wrap {
        margin: 5px 0;
        border-radius: 8px;
        overflow: hidden;
        background: #1a1a3a;
    }
    .dist-bar {
        height: 44px;
        min-width: 4%;
        max-width: 100%;
        display: flex;
        align-items: center;
        padding: 0 14px;
        color: white;
        font-weight: 700;
        font-size: 0.9rem;
        transition: width 0.7s ease;
        border-radius: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ── Leaderboard rows ── */
    .lb {
        padding: 12px 20px;
        margin: 5px 0;
        border-radius: 10px;
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .lb-me {
        outline: 2px solid #1368ce;
        outline-offset: 2px;
    }

    /* ── Podium ── */
    .podium {
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 14px;
        margin: 28px 0 8px 0;
    }
    .podium-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        border-radius: 10px 10px 0 0;
        color: white;
        font-weight: 700;
        text-align: center;
        padding: 14px 22px;
        min-width: 110px;
        box-shadow: 0 -4px 16px rgba(0,0,0,0.3);
    }

    /* ── Join page subtitle ── */
    .subtitle {
        color: #8888bb;
        font-size: 0.95rem;
        margin-top: -12px;
        margin-bottom: 24px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)


# ── HOST VIEWS ────────────────────────────────────────────────────────────────
def host_lobby(conn):
    st.title("🎯 IR & RS Quiz — Host Panel")
    players = get_players(conn)

    col_info, col_count = st.columns([3, 1])
    with col_info:
        st.markdown("Share the **player URL** (without `?host=true`) with your students.")
    with col_count:
        st.metric("Players joined", len(players))

    if players:
        cols = st.columns(4)
        for i, p in enumerate(players):
            with cols[i % 4]:
                st.markdown(f"✅ **{p['name']}**")
    else:
        st.info("⏳ Waiting for students to join…")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 Start Game", type="primary", disabled=not players, use_container_width=True):
            set_phase(conn, "question", q_idx=0, q_start=time.time())
            st.rerun()
    with c2:
        if st.button("🔄 Reset / Clear All", use_container_width=True):
            reset_game(conn)
            st.rerun()

    time.sleep(POLL_INTERVAL)
    st.rerun()


def host_question(conn, s):
    q_idx              = s["q_idx"]
    q_text, opts, correct, _ = QUESTIONS[q_idx]
    remaining          = max(0.0, QUESTION_TIME - (time.time() - s["q_start"]))

    if remaining == 0:
        set_phase(conn, "results")
        st.rerun()

    st.markdown(
        f'<div class="q-badge">Q{q_idx + 1} / {len(QUESTIONS)}</div>',
        unsafe_allow_html=True,
    )
    render_timer(remaining)
    st.markdown(f'<div class="q-box">{q_text}</div>', unsafe_allow_html=True)

    all_ans = q_answers(conn, q_idx)
    players  = get_players(conn)

    # ── Only show count — NO distribution during live question ────────────────
    st.metric("Answers received", f"{len(all_ans)} / {len(players)}")

    st.divider()
    if st.button("⏭ Show Results Now", use_container_width=True):
        set_phase(conn, "results")
        st.rerun()

    time.sleep(POLL_INTERVAL)
    st.rerun()


def host_results(conn, s):
    q_idx                    = s["q_idx"]
    q_text, opts, correct, explanation = QUESTIONS[q_idx]

    st.markdown(
        f'<div class="q-badge">Q{q_idx + 1} / {len(QUESTIONS)} — Results</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="q-box">{q_text}</div>', unsafe_allow_html=True)
    st.success(f"✅ Correct answer: **{opts[correct - 1]}**")

    all_ans   = q_answers(conn, q_idx)
    n_correct = sum(1 for a in all_ans if a["correct"])

    # ── Distribution + explanation (only shown now, not during question) ──────
    render_distribution(all_ans, opts, correct)
    render_explanation(explanation)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Correct", f"{n_correct} / {len(all_ans)}")

    if all_ans:
        st.markdown("**This round:**")
        for a in sorted(all_ans, key=lambda x: -x["pts"])[:8]:
            icon = "✅" if a["correct"] else "❌"
            st.write(f"{icon} **{a['player']}**  +{a['pts']} pts")

    st.divider()
    st.subheader("🏆 Standings")
    render_leaderboard(get_players(conn))

    st.divider()
    is_last = (q_idx + 1) >= len(QUESTIONS)
    if is_last:
        if st.button("🏁 End Game", type="primary", use_container_width=True):
            set_phase(conn, "ended")
            st.rerun()
    else:
        if st.button(
            f"▶ Next Question  ({q_idx + 2} / {len(QUESTIONS)})",
            type="primary",
            use_container_width=True,
        ):
            set_phase(conn, "question", q_idx=q_idx + 1, q_start=time.time())
            st.rerun()


def host_ended(conn):
    st.title("🏆 Final Results")
    st.balloons()
    players = get_players(conn)
    render_podium(players)
    render_leaderboard(players, max_rows=20)
    st.divider()
    if st.button("🔄 New Game", use_container_width=True):
        reset_game(conn)
        st.rerun()


# ── PLAYER VIEWS ──────────────────────────────────────────────────────────────
def player_lobby(name):
    st.title("🎯 IR & RS Quiz")
    st.success(f"Welcome **{name}**! You're in. 👋")
    st.info("⏳ Waiting for the host to start the game…")
    time.sleep(POLL_INTERVAL)
    st.rerun()


def player_question(conn, s, name):
    q_idx              = s["q_idx"]
    q_text, opts, correct, _ = QUESTIONS[q_idx]
    remaining          = max(0.0, QUESTION_TIME - (time.time() - s["q_start"]))
    already            = has_answered(conn, name, q_idx)

    st.markdown(
        f'<div class="q-badge">Q{q_idx + 1} / {len(QUESTIONS)}</div>',
        unsafe_allow_html=True,
    )
    render_timer(remaining)
    st.markdown(f'<div class="q-box">{q_text}</div>', unsafe_allow_html=True)

    if already:
        st.markdown(
            '<div class="locked-card">✅<br>Answer locked in!<br>'
            '<span style="font-size:1rem;font-weight:400">Waiting for results…</span></div>',
            unsafe_allow_html=True,
        )
    elif remaining == 0:
        st.warning("⏰ Time's up!")
    else:
        # ── The ONLY st.columns call on this page — enables colour CSS ────────
        c1, c2, c3, c4 = st.columns(4)
        for col, idx in zip([c1, c2, c3, c4], range(4)):
            with col:
                if st.button(
                    f"{SHAPES[idx]}  {opts[idx]}",
                    key=f"ans_{idx}",
                    use_container_width=True,
                ):
                    is_correct = (idx + 1) == correct
                    pts = calc_pts(remaining) if is_correct else 0
                    submit_answer(conn, name, q_idx, idx + 1, is_correct, pts)
                    st.rerun()

    time.sleep(POLL_INTERVAL)
    st.rerun()


def player_results(conn, s, name):
    q_idx                    = s["q_idx"]
    q_text, opts, correct, explanation = QUESTIONS[q_idx]

    st.markdown(
        f'<div class="q-badge">Q{q_idx + 1} — Results</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="q-box">{q_text}</div>', unsafe_allow_html=True)

    my_ans = conn.execute(
        "SELECT * FROM answers WHERE player=? AND q_idx=?", (name, q_idx)
    ).fetchone()

    if my_ans:
        if my_ans["correct"]:
            st.success(f"✅ Correct!  +{my_ans['pts']} points")
            st.balloons()
        else:
            st.error("❌ Wrong!")
            st.info(f"Correct answer: **{opts[correct - 1]}**")
    else:
        st.warning("⏰ You didn't answer in time.")
        st.info(f"Correct answer: **{opts[correct - 1]}**")

    # ── Distribution + explanation ────────────────────────────────────────────
    all_ans = q_answers(conn, q_idx)
    render_distribution(all_ans, opts, correct)
    render_explanation(explanation)

    row     = conn.execute("SELECT score FROM players WHERE name=?", (name,)).fetchone()
    score   = row["score"] if row else 0
    players = get_players(conn)
    rank    = next((i + 1 for i, p in enumerate(players) if p["name"] == name), None)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Your score", score)
    with c2:
        if rank:
            st.metric("Your rank", f"#{rank} / {len(players)}")

    st.info("⏳ Waiting for the host to continue…")
    time.sleep(POLL_INTERVAL)
    st.rerun()


def player_ended(conn, name):
    players = get_players(conn)
    rank    = next((i + 1 for i, p in enumerate(players) if p["name"] == name), None)
    score   = next((p["score"] for p in players if p["name"] == name), 0)
    medals  = ["🥇", "🥈", "🥉"]

    st.title("🏆 Game Over!")
    if rank and rank <= 3:
        st.markdown(f"## {medals[rank - 1]} You finished #{rank}!")
    else:
        st.markdown(f"## You finished #{rank}!")

    st.metric("Final score", score)
    render_podium(players)

    st.divider()
    st.subheader("Final Leaderboard")
    render_leaderboard(players, highlight_name=name, max_rows=len(players))


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="IR & RS Quiz",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()
    conn    = get_conn()
    is_host = "host" in st.query_params

    # ── HOST ──────────────────────────────────────────────────────────────────
    if is_host:
        if not st.session_state.get("host_auth"):
            st.title("🔐 Host Login")
            st.markdown('<p class="subtitle">Information Retrieval & Recommender Systems · TAU 2026</p>',
                        unsafe_allow_html=True)
            pwd = st.text_input("Password", type="password")
            if st.button("Login", type="primary"):
                if pwd == HOST_PASSWORD:
                    st.session_state.host_auth = True
                    st.rerun()
                else:
                    st.error("Wrong password")
            return

        s     = get_state(conn)
        phase = s["phase"]
        if   phase == "lobby":    host_lobby(conn)
        elif phase == "question": host_question(conn, s)
        elif phase == "results":  host_results(conn, s)
        elif phase == "ended":    host_ended(conn)

    # ── PLAYER ────────────────────────────────────────────────────────────────
    else:
        if "player_name" not in st.session_state:
            st.title("🎯 IR & RS Quiz")
            st.markdown(
                '<p class="subtitle">Information Retrieval & Recommender Systems · TAU 2026</p>',
                unsafe_allow_html=True,
            )

            s = get_state(conn)
            if s["phase"] != "lobby":
                st.warning("🎮 A game is in progress. Please wait for the next round!")
                time.sleep(POLL_INTERVAL)
                st.rerun()
                return

            st.markdown("### Enter your name to join")
            name_input = st.text_input("Your name", max_chars=20, placeholder="e.g. Alice")
            if st.button("Join Game 🚀", type="primary", use_container_width=True):
                name_input = name_input.strip()
                if not name_input:
                    st.error("Please enter a name")
                elif not join_game(conn, name_input):
                    st.error("That name is already taken — choose another")
                else:
                    st.session_state.player_name = name_input
                    st.rerun()
            return

        name  = st.session_state.player_name
        s     = get_state(conn)
        phase = s["phase"]
        if   phase == "lobby":    player_lobby(name)
        elif phase == "question": player_question(conn, s, name)
        elif phase == "results":  player_results(conn, s, name)
        elif phase == "ended":    player_ended(conn, name)


if __name__ == "__main__":
    main()
