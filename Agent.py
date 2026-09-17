import os
import random
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph,START, END
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler
from typing import TypedDict, List, Dict, Any, Optional, Literal


load_dotenv()

# Weaviate Initialization
import math
import weaviate
from weaviate.classes.init import Auth
from weaviate.util import generate_uuid5
from weaviate.classes.config import Configure, Property, DataType

env_path = '.env'
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
headers = {"X-Cohere-Api-Key": os.getenv("COHERE_APIKEY")}
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers=headers
)
print(client.is_ready())
################################

langfuse_handler = CallbackHandler()
TOTAL_ROUNDS = 5
DB_PATH = './jlpt_agent.db'


def get_vocab_words(lesson_number=None, jlpt_level=None, limit=TOTAL_ROUNDS):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = "SELECT id,word, reading, meaning, accepted_answers FROM vocabulary"
    conditions = []
    params = []

    if lesson_number is not None:
        conditions.append(
            "genki_lesson_id = (SELECT id FROM lessons WHERE lesson_number = ?)"
        )
        params.append(lesson_number)

    if jlpt_level is not None:
        conditions.append("jlpt_level = ?")
        params.append(jlpt_level)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(limit)

    rows = cur.execute(query, params).fetchall()
    conn.close()

    words = []
    for row in rows:
        words.append({
            "vocabulary_id": row["id"],
            "word": row["word"],
            "reading": row["reading"],
            "meaning": row["meaning"],
            "accepted": row["accepted_answers"].split(",") if row["accepted_answers"] else [],
        })

    return words

class LearningState(TypedDict):
    score: int
    userid: int
    feedback: str
    username: str
    user_answer: str
    is_correct: bool
    round_number: int
    current_word: dict
    remaining_words: list
    kanjis: list

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

def get_or_create_user(state: LearningState):
    name = input("Enter your name: ").strip()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM users WHERE name = ?", (name,))
    user = cur.fetchone()

    if user is not None:
        print(f"Welcome back, {user['name']}!")
        conn.close()
        return {**state, "userid": user["id"], "username": user["name"]}
    
    confirm = input(f"No account found for '{name}'. Create one? (Y/N): ").strip().upper()

    if confirm != "Y":
        name = input("Enter the name you want to use: ").strip()

    cur.execute("INSERT OR IGNORE INTO users (name) VALUES (?)", (name,))
    conn.commit()

    cur.execute("SELECT id, name FROM users WHERE name = ?", (name,))
    user = cur.fetchone()
    conn.close()

    print(f"New account created for {user['name']}.")
    return {**state, "userid": user["id"], "username": user["name"]}

def get_daily_session(userid: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    current_lesson = cur.execute("SELECT current_lesson FROM users WHERE id = ?",(userid,)).fetchone()[0]

    # Retrieving Review Words
    review_words = cur.execute("""
        SELECT v.id, v.word, v.reading, v.meaning, v.accepted_answers
        FROM learner_vocabulary lv
        JOIN vocabulary v ON v.id = lv.vocabulary_id
        WHERE lv.user_id = ?
        AND lv.mastery < 0.8 AND DATE(lv.next_review) <= DATE('now')
        ORDER BY lv.mastery ASC
    """,(userid,)).fetchall()

    # Retrieving Todays Words
    total_vocab = cur.execute("""
        SELECT COUNT(*) FROM vocabulary
        WHERE genki_lesson_id = (SELECT id FROM lessons WHERE lesson_number =?)
    """,(current_lesson,)).fetchone()[0]

    daily_vocab_limit = math.ceil(total_vocab / 5) if total_vocab else 0

    new_vocab_rows = cur.execute("""
        SELECT v.id, v.word, v.reading, v.meaning, v.accepted_answers
        FROM vocabulary v
        LEFT JOIN learner_vocabulary lv
        ON lv.vocabulary_id = v.id AND lv.user_id = ?
        WHERE v.genki_lesson_id = (SELECT id FROM lessons WHERE lesson_number = ?)
        AND lv.vocabulary_id IS NULL
        ORDER BY v.id
        LIMIT ?
    """,(userid, current_lesson, daily_vocab_limit)).fetchall()

    # Retriving Kanji
    total_kanji = cur.execute("""
        SELECT COUNT(*) FROM kanji
        WHERE genki_lesson_id = (SELECT id FROM lessons WHERE lesson_number = ?)
    """, (current_lesson,)).fetchone()[0]

    daily_kanji_limit = math.ceil(total_kanji / 5) if total_kanji else 0

    new_kanji_rows = cur.execute("""
        SELECT k.id, k.character, k.meaning, k.onyomi, k.kunyomi, k.accepted_answers
        FROM kanji k
        LEFT JOIN learner_kanji lk
            ON lk.kanji_id = k.id AND lk.user_id = ?
        WHERE k.genki_lesson_id = (SELECT id FROM lessons WHERE lesson_number = ?)
          AND lk.kanji_id IS NULL
        ORDER BY k.id
        LIMIT ?
    """, (userid, current_lesson, daily_kanji_limit)).fetchall()

    # Retriving Grammar Paterns
    grammar_rows = cur.execute("""
        SELECT id, pattern, meaning, formation, usage_notes,
               common_mistakes, accepted_answers
        FROM grammar
        WHERE genki_lesson_id = (SELECT id FROM lessons WHERE lesson_number = ?)
        ORDER BY id
    """, (current_lesson,)).fetchall()

    conn.close()

    def to_vocab(row):
        return {
            "vocabulary_id": row["id"],
            "word": row["word"],
            "reading": row["reading"],
            "meaning": row["meaning"],
            "accepted": row["accepted_answers"].split(",") if row["accepted_answers"] else [],
            "type": "vocabulary",
        }

    def to_kanji(row):
        return {
            "kanji_id": row["id"],
            "character": row["character"],
            "meaning": row["meaning"],
            "onyomi": row["onyomi"],
            "kunyomi": row["kunyomi"],
            "accepted": row["accepted_answers"].split(",") if row["accepted_answers"] else [],
            "type": "kanji",
        }
    
    def to_grammar(row):
        return {
            "grammar_id": row["id"],
            "pattern": row["pattern"],
            "meaning": row["meaning"],
            "formation": row["formation"],
            "usage_notes": row["usage_notes"],
            "common_mistakes": row["common_mistakes"],
            "accepted": row["accepted_answers"].split(",") if row["accepted_answers"] else [],
            "type": "grammar",
        }
    return {
        "current_lesson": current_lesson,
        "review":         [to_vocab(r) for r in review_words],
        "new_vocab":      [to_vocab(r) for r in new_vocab_rows],
        "new_kanji":      [to_kanji(r) for r in new_kanji_rows],
        "grammar":        [to_grammar(r) for r in grammar_rows],
    }

def plan_daily_session(state: LearningState) -> LearningState:
    session =  get_daily_session(state["userid"])
    print(f"\n📚 Today's Session — Lesson {session['current_lesson']}")
    print(f"   Review words : {len(session['review'])}")
    print(f"   New vocab    : {len(session['new_vocab'])}")
    print(f"   New kanji    : {len(session['new_kanji'])}")
    print(f"   Grammar      : {len(session['grammar'])} pattern(s)")

    print(session["new_kanji"])
    all_items = session["review"] + session["new_vocab"]

    if not all_items:
        return {**state,"remaining_words": [],"grammar_items": session["grammar"],"current_lesson": session["current_lesson"],}

    return {**state,"remaining_words": all_items,"grammar_items":   session["grammar"],"current_lesson":  session["current_lesson"],"kanjis": session["new_kanji"],}

def ask_question(state: LearningState):
    if not state["remaining_words"]:
        print("No vocabulary available for today's session.")
        return state
    word = state["remaining_words"][0] 
    remaining = state["remaining_words"][1:]

    print(f"\n--- Round {state['round_number']} ---")
    print(f"What does this word mean?  {word['word']} ({word['reading']})")

    return {**state, "current_word": word,"remaining_words": remaining}

def get_user_ans(state: LearningState):
    answer = input("Enter your answer: ").strip()
    return {**state, "user_answer": answer}

def evaluate(state: LearningState):
    word = state["current_word"]
    prompt = (
        "You are grading a Japanese vocabulary quiz answer.\n"
        f"Word: {word['word']} ({word['reading']})\n"
        f"Correct meaning: {word['meaning']}\n"
        f"Student's answer: {state['user_answer']}\n\n"
        "Is the student's answer semantically correct, even if worded "
        "differently or with minor spelling issues? "
        "Reply with exactly one word: CORRECT or WRONG."
    )
    res = model.invoke(prompt)
    # print('Tokens Wasted: ',res.total_tokens)
    if isinstance(res.content, str):
        verdict = res.content.strip().upper()
    else:
        verdict = "".join(
            block.get("text", "")
            for block in res.content
            if isinstance(block, dict)
        ).strip().upper()
    is_correct = verdict.startswith("CORRECT")

    return {**state, "is_correct": is_correct}

def evaluate_multiway(state: LearningState):
    weaviateVocab = client.collections.get('JapaneseVocab')

    response = weaviateVocab.query.near_text(
        query=state['user_answer'],
        limit=1,
        return_properties=["word","meaning"],
        return_metadata=["distance"]
    )

    if not response.objects:
        return {**state, "is_correct": False}

    result = response.objects[0]
    distance = result.metadata.distance
    matched_meaning = result.properties["meaning"]
    correct_meaning = state["current_word"]["meaning"]
    if matched_meaning == correct_meaning and distance < 0.7:
        return {**state, "is_correct": True}

    return {**state, "is_correct": False}

def correct_feedback(state: LearningState):
    print(f"Correct! {state['current_word']['word']} = {state['current_word']['meaning']}")
    return {**state, "score": state["score"] + 1, "round_number": state["round_number"] + 1}
 
 
def wrong_feedback(state: LearningState):
    print(f"Not quite. {state['current_word']['word']} = {state['current_word']['meaning']}")
    return {**state, "round_number": state["round_number"] + 1}
 
 
def show_results(state: LearningState):
    print("\n--- Quiz complete ---")
    print(f"Score: {state['score']} / {TOTAL_ROUNDS}")
    return state



def route_on_correctness(state: LearningState) -> Literal["correct", "wrong"]:
    return "correct" if state["is_correct"] else "wrong"

def route_next_round(state: LearningState) -> Literal["continue", "end"]:
    if state["round_number"] > TOTAL_ROUNDS or not state["remaining_words"]:
        return "end"
    return "continue"

def record_attempt(user_id: int, vocabulary_id: int, is_correct: int, user_answer: str, correct_answer: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    correct_increment = 1 if is_correct else 0

    cur.execute("""
        INSERT INTO learner_vocabulary
            (user_id, vocabulary_id, attempts, correct_attempts,
             incorrect_attempts, mastery, last_reviewed, next_review, introduced_on)
        VALUES
            (?, ?, 1, ?, ?, ?, CURRENT_TIMESTAMP, DATE('now', '+1 day'), DATE('now'))
        ON CONFLICT(user_id, vocabulary_id) DO UPDATE SET
            attempts           = attempts + 1,
            correct_attempts   = correct_attempts + ?,
            incorrect_attempts = incorrect_attempts + ?,
            mastery            = (correct_attempts + ?) * 1.0 / (attempts + 1),
            last_reviewed      = CURRENT_TIMESTAMP,
            next_review        = DATE('now', '+1 day')
    """, (user_id, vocabulary_id, correct_increment,1 - correct_increment,float(correct_increment),correct_increment,1 - correct_increment,correct_increment))

    if not is_correct:
        cur.execute("INSERT INTO mistakes (user_id, item_type, item_id, user_answer, correct_answer) VALUES (?, 'vocabulary', ?, ?, ?)", (user_id, vocabulary_id, user_answer, correct_answer))

    conn.commit()
    conn.close()

def record_result(state: LearningState):
    record_attempt(
        user_id       = state["userid"],
        vocabulary_id = state["current_word"]["vocabulary_id"],
        is_correct    = state["is_correct"],
        user_answer   = state["user_answer"],
        correct_answer= state["current_word"]["meaning"],
    )
    return state

def build_graph():
    graph =  StateGraph(LearningState)

    graph.add_node("get_or_create_user",get_or_create_user)
    graph.add_node("plan_daily_session",plan_daily_session)
    graph.add_node("ask_question",ask_question)

    graph.add_node("get_user_ans", get_user_ans)
    graph.add_node("evaluate_multiway",evaluate_multiway)
    graph.add_node("correct_feedback", correct_feedback)
    graph.add_node("wrong_feedback", wrong_feedback)
    graph.add_node("show_results", show_results)
    graph.add_node("record_result", record_result)

    graph.set_entry_point("get_or_create_user")

    graph.add_edge("get_or_create_user","plan_daily_session")
    graph.add_edge("plan_daily_session","ask_question")
    graph.add_edge("ask_question","get_user_ans")
    graph.add_edge("get_user_ans","evaluate_multiway")
    graph.add_edge("evaluate_multiway", "record_result")

    graph.add_conditional_edges("record_result",route_on_correctness,{"correct": "correct_feedback", "wrong": "wrong_feedback"})
    graph.add_conditional_edges("correct_feedback",route_next_round,{"continue": "ask_question", "end": "show_results"},)
    graph.add_conditional_edges("wrong_feedback",route_next_round,{"continue": "ask_question", "end": "show_results"},)
    graph.add_edge("show_results",END)

    return graph.compile()


def main():
    if not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit(
            "Missing GOOGLE_API_KEY. Create a .env file (see .env.example) "
            "with your Gemini API key before running."
        )
 
    app = build_graph()

    words = get_vocab_words(13, "N4", TOTAL_ROUNDS)

    initial_state: LearningState = {
        "remaining_words": words,
        "current_word": {},
        "user_answer": "",
        "is_correct": False,
        "feedback": "",
        "round_number": 1,
        "score": 0,
        "userid": 0,
        "username": "",
    }
    try:
        app.invoke(initial_state)
    finally:
        client.close()
        
if __name__ == "__main__":
    main()