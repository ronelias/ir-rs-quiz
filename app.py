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
QUESTION_TIME = 30        # seconds per question
HOST_PASSWORD = "prof2026"
POLL_INTERVAL = 1.5       # seconds between auto-refresh
DB_PATH       = Path("quiz.db")

COLORS = ["#e21b3c", "#1368ce", "#d89e00", "#26890c"]  # red, blue, yellow, green
SHAPES = ["▲", "◆", "●", "✕"]

QUESTIONS = [
    # (question_text, [answer1, answer2, answer3, answer4], correct_1_based)

    # ── L1: IR Introduction ───────────────────────────────────────────────────
    ("Which of the following best describes unstructured data?",
     ["Data stored in relational database tables",
      "Free text documents like emails and web pages",
      "XML files with defined schemas",
      "Spreadsheets with labeled columns"], 2),

    ("What is the main goal of an Information Retrieval system?",
     ["To store data efficiently in a database",
      "To encrypt sensitive documents",
      "To find material satisfying an information need from a large collection",
      "To compress large document collections"], 3),

    ("An IR system is formally defined by three components. Which answer correctly lists them?",
     ["Crawler, parser, and compressor",
      "Tokenizer, stemmer, and stop-word list",
      "Representation of queries, documents, and a ranking/relevance function",
      "Database schema, query optimizer, and result cache"], 3),

    # ── L2: Boolean Model ─────────────────────────────────────────────────────
    ("In the fuzzy/extended Boolean model, how are term weights typically represented?",
     ["As integers (0, 1, 2, 3...)",
      "As real-valued scores between 0 and 1",
      "As binary bit strings",
      "As negative values for irrelevant terms"], 2),

    # ── L3: Vector Space Model ────────────────────────────────────────────────
    ("In the Vector Space Model, documents and queries are represented as:",
     ["Binary bit vectors",
      "Relational tables",
      "Weighted term vectors in a high-dimensional space",
      "Linked lists of tokens"], 3),

    ("The IDF (Inverse Document Frequency) of a term is HIGH when:",
     ["The term appears in many documents",
      "The term appears in very few documents",
      "The term has high within-document frequency",
      "The term is a stop word"], 2),

    ("Cosine similarity between two document vectors is computed as:",
     ["The dot product of raw term frequencies",
      "The Euclidean distance between vectors",
      "Dot product of normalized vectors divided by product of their magnitudes",
      "Sum of absolute differences between vector components"], 3),

    ("Why do we normalize document vectors by their length in cosine similarity?",
     ["To make all term weights positive",
      "To remove stop words from the computation",
      "To neutralize the effect of document length on similarity",
      "To increase the speed of index lookup"], 3),

    # ── L4: Text Operations ───────────────────────────────────────────────────
    ("Tokenization is the process of:",
     ["Ranking documents by relevance score",
      "Breaking a text stream into individual terms/tokens",
      "Removing duplicate documents from a collection",
      "Compressing index files"], 2),

    ("Zipf's Law states that:",
     ["Term frequency grows logarithmically with collection size",
      "The product of a term's rank and its frequency is approximately constant",
      "Rare words carry more meaning than common words",
      "Most documents contain fewer than 100 unique terms"], 2),

    ("The Porter Stemming algorithm works by:",
     ["Looking up words in a dictionary of canonical forms",
      "Applying a series of suffix-stripping rules",
      "Using machine learning to predict word roots",
      "Replacing all words with their phonetic codes"], 2),

    ("In the Noisy Channel model, the system selects the correction that maximizes:",
     ["Edit distance to the original word",
      "Term frequency in the index",
      "P(word) x P(observed|word) - prior times channel probability",
      "The number of vowels in the candidate word"], 3),

    ("Edit distance (Levenshtein) counts the minimum number of:",
     ["Characters in the longer word",
      "Insertions, deletions, and substitutions to transform one string to another",
      "Shared substrings between two words",
      "Vowel differences between two words"], 2),

    # ── L5: Indexing ──────────────────────────────────────────────────────────
    ("The three steps for constructing an inverted index - what does each step do?",
     ["Crawl (fetch pages) -> Compress (shrink) -> Query (answer requests)",
      "Tokenize -> Sort (order term-docID pairs) -> Group/merge (posting lists)",
      "Parse (read docs) -> Rank (score by TF-IDF) -> Store (write to disk)",
      "Stem (normalize) -> Weight (TF-IDF) -> Cluster (group similar docs)"], 2),

    ("A positional index stores, for each term:",
     ["Only the list of documents containing that term",
      "Document IDs and positions of each occurrence within each document",
      "The TF-IDF weight of the term per document",
      "The number of documents in which the term appears"], 2),

    ("Heaps' Law describes the relationship between:",
     ["Term frequency and document frequency",
      "Collection size and vocabulary size - vocabulary grows sub-linearly",
      "Index size and query response time",
      "Number of documents and average document length"], 2),

    ("In BSBI (Block Sort-Based Indexing), blocks are processed because:",
     ["The full collection fits easily in RAM",
      "Collection does not fit in RAM; each block is sorted then merged",
      "MapReduce requires fixed-size input blocks",
      "Positional indexes must be built incrementally"], 2),

    ("A biword index stores:",
     ["Single terms only",
      "Consecutive pairs of terms as index entries",
      "All n-grams up to length 5",
      "Character-level bigrams for fuzzy matching"], 2),

    # ── L6: IR Evaluation ─────────────────────────────────────────────────────
    ("Precision is defined as:",
     ["Relevant retrieved / Total relevant in collection",
      "Relevant retrieved / Total retrieved",
      "Total retrieved / Collection size",
      "Relevant in collection / Collection size"], 2),

    ("Recall is defined as:",
     ["Relevant retrieved / Total retrieved",
      "Relevant retrieved / Total relevant documents in collection",
      "Total documents in collection / Relevant retrieved",
      "Precision x F-measure"], 2),

    ("Mean Average Precision (MAP) is computed by:",
     ["Averaging precision at a fixed cutoff (P@10) across queries",
      "Computing precision only for the top-ranked document",
      "Averaging the Average Precision scores across all queries",
      "Taking the harmonic mean of precision and recall"], 3),

    ("In DCG, relevance at lower ranks is discounted by:",
     ["Subtracting the rank number from the gain",
      "Dividing the gain by the logarithm of the rank position",
      "Multiplying the gain by (1/rank squared)",
      "Ignoring all results below rank 10"], 2),

    ("Mean Reciprocal Rank (MRR) is most appropriate when:",
     ["All returned documents are equally relevant",
      "You care about the rank of the first relevant document",
      "The collection has no relevant documents",
      "You need to evaluate multi-label ranked lists"], 2),

    ("Inter-annotator agreement in relevance judgments is typically measured using:",
     ["F-measure",
      "Cohen's Kappa",
      "NDCG",
      "MAP"], 2),

    # ── L7: RS Introduction ───────────────────────────────────────────────────
    ("Which type of filtering recommends items based on the preferences of similar users?",
     ["Content-based filtering",
      "Collaborative filtering",
      "Knowledge-based filtering",
      "Demographic filtering"], 2),

    ("Content-based filtering recommends items by:",
     ["Finding users with similar rating histories",
      "Analyzing item features and matching them to the user's past preferences",
      "Using explicit rules from domain experts",
      "Randomly sampling popular items"], 2),

    ("A major advantage of hybrid recommender systems is:",
     ["They are always faster than pure approaches",
      "They combine multiple paradigms to overcome individual weaknesses",
      "They require no user data",
      "They only work for movie recommendations"], 2),

    ("The cold start problem in recommender systems occurs when:",
     ["The server runs out of memory during recommendation",
      "A new user or item has little or no interaction history",
      "The recommendation algorithm converges too slowly",
      "The item catalog is too large to process"], 2),

    # ── L8: Collaborative Filtering ───────────────────────────────────────────
    ("In user-based k-NN CF, similarity between users is most commonly measured with:",
     ["Cosine similarity on raw ratings",
      "Euclidean distance on item features",
      "Pearson correlation on co-rated items",
      "Jaccard index on purchased items"], 3),

    ("The Pearson correlation between users u and v is +1 when:",
     ["They rated exactly the same items",
      "Their ratings are perfectly linearly related (same relative pattern)",
      "They both rated all items with 5 stars",
      "Their average ratings are identical"], 2),

    ("Item-based CF predicts a rating using:",
     ["The user's average rating only",
      "Ratings given by the same user to similar items",
      "The global average item rating",
      "The popularity rank of each item"], 2),

    ("Slope One predicts a rating by:",
     ["Using matrix factorization of the rating matrix",
      "Learning user and item bias terms with gradient descent",
      "Computing weighted average deviations between co-rated item pairs",
      "Applying association rules from frequent itemsets"], 3),

    ("In SVD-based matrix factorization, the rating matrix R is approximated as:",
     ["R = U x I where U and I are binary matrices",
      "R = P x Q^T where P and Q are low-rank latent factor matrices",
      "R = the average of user and item mean ratings",
      "R = a diagonal matrix of singular values only"], 2),

    ("An association rule A->B in recommender systems means:",
     ["Buying A causes the user to buy B",
      "Users who liked A tend to also like B with measurable support/confidence",
      "Item A is always more popular than item B",
      "A and B share the same content features"], 2),

    ("High support for a rule {A, B} means:",
     ["Users rate both A and B with 5 stars",
      "A large proportion of users have interacted with both A and B",
      "The rule has high precision",
      "A predicts B with 100% confidence"], 2),
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
        return False  # name taken

def submit_answer(conn, player, q_idx, choice, correct, pts):
    try:
        conn.execute(
            "INSERT INTO answers VALUES (?,?,?,?,?,?)",
            (player, q_idx, choice, int(correct), pts, time.time())
        )
        conn.execute(
            "UPDATE players SET score=score+? WHERE name=?", (pts, player)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # already answered

def has_answered(conn, player, q_idx):
    return conn.execute(
        "SELECT 1 FROM answers WHERE player=? AND q_idx=?", (player, q_idx)
    ).fetchone() is not None

def q_answers(conn, q_idx):
    return conn.execute(
        "SELECT * FROM answers WHERE q_idx=?", (q_idx,)
    ).fetchall()

def reset_game(conn):
    conn.executescript("""
        DELETE FROM players;
        DELETE FROM answers;
        UPDATE state SET phase='lobby', q_idx=0, q_start=0 WHERE id=1;
    """)
    conn.commit()

def calc_pts(remaining):
    return int(500 + 500 * max(0.0, remaining / QUESTION_TIME))


# ── STYLING ───────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    .q-box {
        background: #2c2c54; color: white;
        padding: 28px; border-radius: 12px;
        font-size: 1.5rem; font-weight: bold;
        text-align: center; margin-bottom: 24px;
        line-height: 1.4;
    }
    /* Color answer buttons by column position */
    div[data-testid="column"]:nth-of-type(1) button {
        background: #e21b3c !important; color: white !important;
        min-height: 90px; font-size: 1rem; font-weight: bold; border-radius: 8px;
        white-space: normal !important; word-wrap: break-word;
    }
    div[data-testid="column"]:nth-of-type(2) button {
        background: #1368ce !important; color: white !important;
        min-height: 90px; font-size: 1rem; font-weight: bold; border-radius: 8px;
        white-space: normal !important; word-wrap: break-word;
    }
    div[data-testid="column"]:nth-of-type(3) button {
        background: #d89e00 !important; color: white !important;
        min-height: 90px; font-size: 1rem; font-weight: bold; border-radius: 8px;
        white-space: normal !important; word-wrap: break-word;
    }
    div[data-testid="column"]:nth-of-type(4) button {
        background: #26890c !important; color: white !important;
        min-height: 90px; font-size: 1rem; font-weight: bold; border-radius: 8px;
        white-space: normal !important; word-wrap: break-word;
    }
    .lb {
        padding: 10px 18px; margin: 5px 0; border-radius: 8px;
        font-size: 1.1rem; font-weight: bold; color: #111;
    }
    </style>
    """, unsafe_allow_html=True)


# ── HOST VIEWS ────────────────────────────────────────────────────────────────
def host_lobby(conn):
    st.title("🎯 IR & RS Quiz — Host Panel")
    players = get_players(conn)
    st.subheader(f"Players joined: {len(players)}")
    for p in players:
        st.write(f"✅ {p['name']}")
    if not players:
        st.info("Share the app URL with your students and wait for them to join.")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 Start Game", type="primary", disabled=not players):
            set_phase(conn, "question", q_idx=0, q_start=time.time())
            st.rerun()
    with c2:
        if st.button("🔄 Reset / Clear Players"):
            reset_game(conn)
            st.rerun()

    time.sleep(POLL_INTERVAL)
    st.rerun()


def host_question(conn, s):
    q_idx     = s["q_idx"]
    q_text, opts, correct = QUESTIONS[q_idx]
    remaining = max(0.0, QUESTION_TIME - (time.time() - s["q_start"]))

    if remaining == 0:
        set_phase(conn, "results")
        st.rerun()

    st.title(f"Question {q_idx + 1} / {len(QUESTIONS)}")
    st.markdown(f'<div class="q-box">{q_text}</div>', unsafe_allow_html=True)
    st.progress(remaining / QUESTION_TIME, text=f"⏱ {int(remaining)} seconds remaining")

    all_ans = q_answers(conn, q_idx)
    players  = get_players(conn)
    st.metric("Answers received", f"{len(all_ans)} / {len(players)}")

    counts = {i: 0 for i in range(1, 5)}
    for a in all_ans:
        counts[a["choice"]] = counts.get(a["choice"], 0) + 1

    st.markdown("**Live distribution:**")
    for i, (opt, color, shape) in enumerate(zip(opts, COLORS, SHAPES)):
        n   = counts.get(i + 1, 0)
        pct = int(n / max(len(players), 1) * 20)
        bar = "█" * pct + "░" * (20 - pct)
        st.markdown(
            f'<span style="color:{color};font-weight:bold">{shape} {opt[:45]}</span>'
            f' — **{n}** &nbsp;<code>{bar}</code>',
            unsafe_allow_html=True,
        )

    st.divider()
    if st.button("⏭ Show Results Now"):
        set_phase(conn, "results")
        st.rerun()

    time.sleep(POLL_INTERVAL)
    st.rerun()


def host_results(conn, s):
    q_idx              = s["q_idx"]
    q_text, opts, correct = QUESTIONS[q_idx]

    st.title(f"Results — Question {q_idx + 1}")
    st.markdown(f'<div class="q-box">{q_text}</div>', unsafe_allow_html=True)
    st.success(f"✅ Correct answer: **{opts[correct - 1]}**")

    all_ans   = q_answers(conn, q_idx)
    n_correct = sum(1 for a in all_ans if a["correct"])
    st.metric("Correct answers", f"{n_correct} / {len(all_ans)}")

    if all_ans:
        st.markdown("**This round:**")
        for a in sorted(all_ans, key=lambda x: -x["pts"])[:8]:
            icon = "✅" if a["correct"] else "❌"
            st.write(f"{icon} **{a['player']}**  +{a['pts']} pts")

    st.divider()
    st.subheader("🏆 Current Standings")
    medals = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(get_players(conn)[:10]):
        m = medals[i] if i < 3 else f"{i + 1}."
        st.write(f"{m} **{p['name']}** — {p['score']} pts")

    st.divider()
    is_last = (q_idx + 1) >= len(QUESTIONS)
    if is_last:
        if st.button("🏁 End Game", type="primary"):
            set_phase(conn, "ended")
            st.rerun()
    else:
        if st.button(f"▶ Next Question  ({q_idx + 2} / {len(QUESTIONS)})", type="primary"):
            set_phase(conn, "question", q_idx=q_idx + 1, q_start=time.time())
            st.rerun()


def host_ended(conn):
    st.title("🏆 Final Results")
    st.balloons()
    medals = ["🥇", "🥈", "🥉"]
    golds  = ["#FFD700", "#C0C0C0", "#CD7F32"]
    for i, p in enumerate(get_players(conn)):
        m  = medals[i] if i < 3 else f"{i + 1}."
        bg = golds[i]  if i < 3 else "#f0f2f6"
        st.markdown(
            f'<div class="lb" style="background:{bg}">'
            f'{m} {p["name"]} — {p["score"]} pts</div>',
            unsafe_allow_html=True,
        )
    st.divider()
    if st.button("🔄 New Game"):
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
    q_text, opts, correct = QUESTIONS[q_idx]
    remaining          = max(0.0, QUESTION_TIME - (time.time() - s["q_start"]))
    already            = has_answered(conn, name, q_idx)

    st.progress(remaining / QUESTION_TIME, text=f"⏱ {int(remaining)}s")
    st.markdown(f'<div class="q-box">{q_text}</div>', unsafe_allow_html=True)

    if already:
        st.success("✅ Answer locked in! Waiting for results…")
    elif remaining == 0:
        st.warning("⏰ Time's up!")
    else:
        # ── The ONLY st.columns call on this page — enables color CSS ──────
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
    q_idx              = s["q_idx"]
    q_text, opts, correct = QUESTIONS[q_idx]

    st.title(f"Question {q_idx + 1} — Results")
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

    row   = conn.execute("SELECT score FROM players WHERE name=?", (name,)).fetchone()
    score = row["score"] if row else 0
    players = get_players(conn)
    rank  = next((i + 1 for i, p in enumerate(players) if p["name"] == name), None)

    st.metric("Your total score", score)
    if rank:
        st.caption(f"Current rank: #{rank} of {len(players)}")

    st.info("⏳ Waiting for the host to continue…")
    time.sleep(POLL_INTERVAL)
    st.rerun()


def player_ended(conn, name):
    st.title("🏆 Game Over!")
    players = get_players(conn)
    rank  = next((i + 1 for i, p in enumerate(players) if p["name"] == name), None)
    score = next((p["score"] for p in players if p["name"] == name), 0)
    medals = ["🥇", "🥈", "🥉"]
    golds  = ["#FFD700", "#C0C0C0", "#CD7F32"]

    if rank and rank <= 3:
        st.markdown(f"# {medals[rank - 1]} You finished #{rank}!")
    else:
        st.markdown(f"# You finished #{rank}!")
    st.metric("Final score", score)

    st.divider()
    st.subheader("Final Leaderboard")
    for i, p in enumerate(players):
        m  = medals[i] if i < 3 else f"{i + 1}."
        bg = golds[i]  if i < 3 else ("#dceefb" if p["name"] == name else "#f0f2f6")
        st.markdown(
            f'<div class="lb" style="background:{bg}">'
            f'{m} {p["name"]} — {p["score"]} pts</div>',
            unsafe_allow_html=True,
        )


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

            s = get_state(conn)
            if s["phase"] != "lobby":
                st.warning("🎮 A game is in progress. Please wait for the next round!")
                time.sleep(POLL_INTERVAL)
                st.rerun()
                return

            st.markdown("### Enter your name to join")
            name_input = st.text_input("Your name", max_chars=20, placeholder="e.g. Alice")
            if st.button("Join Game 🚀", type="primary"):
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
