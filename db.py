"""
JLPT Japanese Learning Agent
Database + Curriculum Ingestion System

You provide:
    - Lesson information
    - Kanji information
    - Vocabulary reading + meaning + JLPT + lesson + part of speech

The system automatically:
    - Creates/updates lessons
    - Enriches vocabulary using Gemini
    - Determines Japanese written form
    - Generates accepted answers
    - Generates semantic variants
    - Generates example sentences
    - Inserts vocabulary
    - Inserts kanji
    - Automatically creates kanji <-> vocabulary relationships
    - Prevents duplicate records
    - Preserves existing database data

Run:

    python db.py

Requirements:

    pip install google-generativeai python-dotenv

.env:

    GOOGLE_API_KEY=your_gemini_api_key
"""

import os
import json
import sqlite3

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

DB_PATH = "jlpt_agent.db"

MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# GEMINI
# ============================================================

model = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0
)


# ============================================================
# DATABASE SCHEMA
# ============================================================

SCHEMA = """

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY,
    lesson_number INTEGER UNIQUE NOT NULL,
    title TEXT,
    textbook TEXT DEFAULT 'Genki II'
);


CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    reading TEXT NOT NULL,
    meaning TEXT NOT NULL,
    jlpt_level TEXT NOT NULL,
    genki_lesson_id INTEGER REFERENCES lessons(id),
    part_of_speech TEXT NOT NULL,
    example_sentence TEXT NOT NULL DEFAULT '',
    accepted_answers TEXT NOT NULL DEFAULT '',
    semantic_variants TEXT NOT NULL DEFAULT ''
);


CREATE TABLE IF NOT EXISTS kanji (
    id INTEGER PRIMARY KEY,
    character TEXT NOT NULL UNIQUE,
    meaning TEXT NOT NULL,
    onyomi TEXT NOT NULL DEFAULT '',
    kunyomi TEXT NOT NULL DEFAULT '',
    jlpt_level TEXT NOT NULL,
    genki_lesson_id INTEGER REFERENCES lessons(id),
    accepted_answers TEXT NOT NULL DEFAULT ''
);


CREATE TABLE IF NOT EXISTS kanji_vocabulary (
    kanji_id INTEGER REFERENCES kanji(id),
    vocabulary_id INTEGER REFERENCES vocabulary(id),
    PRIMARY KEY (kanji_id, vocabulary_id)
);


CREATE TABLE IF NOT EXISTS grammar (
    id INTEGER PRIMARY KEY,
    pattern TEXT NOT NULL,
    meaning TEXT,
    formation TEXT,
    jlpt_level TEXT,
    genki_lesson_id INTEGER REFERENCES lessons(id),
    usage_notes TEXT,
    common_mistakes TEXT,
    accepted_answers TEXT
);


CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    target_jlpt TEXT DEFAULT 'N4',
    current_lesson INTEGER DEFAULT 13,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS mistakes (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    item_type TEXT,
    item_id INTEGER,
    user_answer TEXT,
    correct_answer TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT 0
);


CREATE TABLE IF NOT EXISTS learner_vocabulary (
    user_id INTEGER REFERENCES users(id),
    vocabulary_id INTEGER REFERENCES vocabulary(id),
    mastery REAL DEFAULT 0.0,
    attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    incorrect_attempts INTEGER DEFAULT 0,
    last_reviewed TIMESTAMP,
    next_review TIMESTAMP,
    introduced_on DATE,
    PRIMARY KEY (user_id, vocabulary_id)
);


CREATE TABLE IF NOT EXISTS learner_kanji (
    user_id INTEGER REFERENCES users(id),
    kanji_id INTEGER REFERENCES kanji(id),
    mastery REAL DEFAULT 0.0,
    attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    incorrect_attempts INTEGER DEFAULT 0,
    last_reviewed TIMESTAMP,
    next_review TIMESTAMP,
    introduced_on DATE,
    PRIMARY KEY (user_id, kanji_id)
);


CREATE TABLE IF NOT EXISTS learner_grammar (
    user_id INTEGER REFERENCES users(id),
    grammar_id INTEGER REFERENCES grammar(id),
    mastery REAL DEFAULT 0.0,
    attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    incorrect_attempts INTEGER DEFAULT 0,
    last_reviewed TIMESTAMP,
    next_review TIMESTAMP,
    PRIMARY KEY (user_id, grammar_id)
);

"""


# ============================================================
# LESSON INPUT
# ============================================================
#
# ONLY ADD NEW LESSONS HERE.
#
# Existing lessons will not be duplicated.
#
# ============================================================

LESSONS = [

    {
        "lesson_number": 13,
        "title": "Interesting Experiences in Japan"
    },

    {
        "lesson_number": 14,
        "title": "Personal Advice Column"
    },

    # Future:
    #
    # {
    #     "lesson_number": 15,
    #     "title": "Lesson 15"
    # },

]


# ============================================================
# KANJI INPUT
# ============================================================
#
# This is the information YOU provide.
#
# You do NOT need to provide:
#
#     id
#     kanji-vocabulary relationships
#
# Those are generated automatically.
#
# ============================================================

KANJI_INPUT = [

    {
        "character": "物",
        "meaning": "thing; stuff",
        "onyomi": "ブツ、モツ",
        "kunyomi": "もの",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "鳥",
        "meaning": "bird",
        "onyomi": "チョウ",
        "kunyomi": "とり",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "料",
        "meaning": "fee; charge",
        "onyomi": "リョウ",
        "kunyomi": "",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "理",
        "meaning": "reason",
        "onyomi": "リ",
        "kunyomi": "",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "特",
        "meaning": "special",
        "onyomi": "トク",
        "kunyomi": "",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "安",
        "meaning": "cheap; inexpensive",
        "onyomi": "アン",
        "kunyomi": "やす",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "飯",
        "meaning": "food; cooked rice",
        "onyomi": "ハン",
        "kunyomi": "めし",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "肉",
        "meaning": "meat",
        "onyomi": "ニク",
        "kunyomi": "",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "悪",
        "meaning": "bad; wrong",
        "onyomi": "アク",
        "kunyomi": "わる",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "体",
        "meaning": "body",
        "onyomi": "タイ",
        "kunyomi": "からだ",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "同",
        "meaning": "same",
        "onyomi": "ドウ",
        "kunyomi": "おな",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "着",
        "meaning": "to wear; to arrive",
        "onyomi": "チャク",
        "kunyomi": "つ、き、ぎ",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "空",
        "meaning": "sky; empty",
        "onyomi": "クウ",
        "kunyomi": "そら、あ、から",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "港",
        "meaning": "port; harbor",
        "onyomi": "コウ",
        "kunyomi": "みなと",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "昼",
        "meaning": "noon; daytime",
        "onyomi": "チュウ",
        "kunyomi": "ひる",
        "jlpt_level": "N4",
        "lesson_number": 13
    },

    {
        "character": "海",
        "meaning": "sea; ocean",
        "onyomi": "カイ",
        "kunyomi": "うみ",
        "jlpt_level": "N4",
        "lesson_number": 13
    }

]


# ============================================================
# VOCABULARY INPUT
# ============================================================
#
# This is ALL you need to provide for vocabulary.
#
# You do NOT provide:
#
#     word
#     example_sentence
#     accepted_answers
#     semantic_variants
#     vocabulary_id
#     kanji relationships
#
# The enrichment system handles them.
#
# ============================================================

VOCAB_INPUT = [

    # ============================================================
    # Nouns
    # ============================================================

    {
        "reading": "おとな",
        "meaning": "adult",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "べんごし",
        "meaning": "lawyer",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "わたくし",
        "meaning": "I (formal)",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "pronoun"
    },

    {
        "reading": "カレー",
        "meaning": "curry",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "こうちゃ",
        "meaning": "black tea",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "きもの",
        "meaning": "kimono; Japanese traditional dress",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "セーター",
        "meaning": "sweater",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "がっき",
        "meaning": "musical instrument",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "からて",
        "meaning": "karate",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "ゴルフ",
        "meaning": "golf",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "バイク",
        "meaning": "motorcycle",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "ぞう",
        "meaning": "elephant",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "からだ",
        "meaning": "body",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "がいこくご",
        "meaning": "foreign language",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "ことば",
        "meaning": "language",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "ぶんぽう",
        "meaning": "grammar",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "アプリ",
        "meaning": "application",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "アパート",
        "meaning": "apartment; smaller apartment building",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "マンション",
        "meaning": "larger apartment building; condominium",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "くうこう",
        "meaning": "airport",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "みせ",
        "meaning": "shop; store",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "ぶっか",
        "meaning": "consumer prices",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "こうこく",
        "meaning": "advertisement",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "ぼしゅう",
        "meaning": "recruitment",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },

    {
        "reading": "やくそく",
        "meaning": "promise; appointment",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "noun"
    },


    # ============================================================
    # い-Adjectives
    # ============================================================

    {
        "reading": "うれしい",
        "meaning": "glad",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "i-adjective"
    },

    {
        "reading": "かなしい",
        "meaning": "sad",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "i-adjective"
    },

    {
        "reading": "きびしい",
        "meaning": "strict",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "i-adjective"
    },

    {
        "reading": "きぶんがわるい",
        "meaning": "to feel sick",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "expression"
    },

    {
        "reading": "からい",
        "meaning": "hot and spicy; salty",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "i-adjective"
    },

    {
        "reading": "すごい",
        "meaning": "incredible; awesome",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "i-adjective"
    },

    {
        "reading": "ちかい",
        "meaning": "close; near",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "i-adjective"
    },


    # ============================================================
    # な-Adjectives
    # ============================================================

    {
        "reading": "いろいろ",
        "meaning": "various; different kinds of",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "na-adjective"
    },

    {
        "reading": "しあわせ",
        "meaning": "happy; lasting happiness",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "na-adjective"
    },

    {
        "reading": "だめ",
        "meaning": "no good",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "na-adjective"
    },


    # ============================================================
    # U-Verbs
    # ============================================================

    {
        "reading": "あむ",
        "meaning": "to knit",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "u-verb"
    },

    {
        "reading": "がんばる",
        "meaning": "to do one's best; to try hard",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "u-verb"
    },

    {
        "reading": "なく",
        "meaning": "to cry",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "u-verb"
    },

    {
        "reading": "みがく",
        "meaning": "to brush (teeth); to polish",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "u-verb"
    },

    {
        "reading": "やくそくをまもる",
        "meaning": "to keep a promise",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "u-verb"
    },


    # ============================================================
    # Irregular Verb
    # ============================================================

    {
        "reading": "かんどうする",
        "meaning": "to be moved; to be touched",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "irregular-verb"
    },


    # ============================================================
    # Adverbs and Other Expressions
    # ============================================================

    {
        "reading": "ぜんぶ",
        "meaning": "all",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "adverb"
    },

    {
        "reading": "とくに",
        "meaning": "especially",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "adverb"
    },

    {
        "reading": "ともうします",
        "meaning": "my name is",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "expression"
    },


    # ============================================================
    # Counters / Numbers — Days
    # ============================================================

    {
        "reading": "いちにち",
        "meaning": "one day",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "ふつか",
        "meaning": "two days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "みっか",
        "meaning": "three days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "よっか",
        "meaning": "four days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "いつか",
        "meaning": "five days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "むいか",
        "meaning": "six days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "なのか",
        "meaning": "seven days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "ようか",
        "meaning": "eight days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "ここのか",
        "meaning": "nine days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    },

    {
        "reading": "とおか",
        "meaning": "ten days",
        "jlpt_level": "N4",
        "lesson_number": 13,
        "part_of_speech": "counter"
    }

]


# ============================================================
# GEMINI VOCABULARY ENRICHMENT - BATCH MODE
# ============================================================

def _clean_gemini_json(content: str) -> str:
    """Remove accidental markdown fences from Gemini JSON output."""
    content = content.strip()

    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    return content


def _response_to_text(response) -> str:
    """Convert LangChain Gemini response content into plain text."""
    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if text:
                    parts.append(str(text))
            elif isinstance(block, str):
                parts.append(block)

        return "".join(parts)

    return str(content)


def enrich_vocabulary_batch(vocab_list: list[dict]) -> list[dict]:
    """
    Enrich ALL new vocabulary items in ONE Gemini request.

    Gemini receives the complete batch and returns one JSON object per
    vocabulary item. An input_id is used instead of relying on output order,
    which makes the mapping safe even when two vocabulary items have the
    same reading.
    """

    if not vocab_list:
        return []

    payload = []

    for index, vocab in enumerate(vocab_list):
        payload.append({
            "input_id": index,
            "reading": vocab["reading"],
            "meaning": vocab["meaning"],
            "jlpt_level": vocab["jlpt_level"],
            "part_of_speech": vocab["part_of_speech"]
        })

    input_json = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are a Japanese language curriculum data processor.

We need to enrich a BATCH of Japanese vocabulary items for a JLPT learning
application.

The user supplied the reading, English meaning, JLPT level and part of speech.
Treat those supplied fields as authoritative. Do NOT change their meaning,
JLPT level, or part of speech.

INPUT VOCABULARY BATCH:
{input_json}

For EVERY input item, generate:

1. word
   - The standard Japanese written form.
   - Use kanji where appropriate.
   - If normally written in hiragana or katakana, preserve that form.

2. reading
   - Preserve the supplied reading.

3. accepted_answers
   - Generate 2-5 genuinely acceptable English answers.
   - These are answers that should reasonably be accepted in a Japanese
     language-learning quiz.
   - Do not add unrelated synonyms.

4. semantic_variants
   - Generate 2-5 short English phrases useful for semantic/vector search.
   - They may be natural learner expressions rather than literal translations.
   - Keep them semantically faithful to the supplied meaning.

5. example_sentence
   - Generate ONE simple, natural Japanese example sentence suitable for a
     JLPT N4 learner.
   - Prefer vocabulary and grammar that an N4 learner can understand.

IMPORTANT RULES:
- Return exactly ONE result for every input item.
- Preserve every input_id exactly.
- Do not omit any input item.
- Do not create additional items.
- Do not change the supplied reading.
- Do not change the supplied meaning.
- Do not change the supplied JLPT level.
- Do not change the supplied part of speech.
- Do not invent unusual meanings.
- Return ONLY valid JSON. No explanation. No markdown.

Required output format:
[
  {{
    "input_id": 0,
    "word": "...",
    "reading": "...",
    "accepted_answers": ["...", "..."],
    "semantic_variants": ["...", "..."],
    "example_sentence": "..."
  }}
]
"""

    print(
        f"\n→ Sending {len(vocab_list)} new vocabulary items to Gemini "
        "in ONE batch request..."
    )

    response = model.invoke(prompt)
    content = _clean_gemini_json(_response_to_text(response))

    try:
        results = json.loads(content)
    except json.JSONDecodeError as e:
        print("\n❌ Gemini returned invalid JSON:")
        print(content)
        raise RuntimeError(
            "Could not parse Gemini batch vocabulary response."
        ) from e

    if not isinstance(results, list):
        raise RuntimeError(
            "Gemini batch response must be a JSON list."
        )

    expected_ids = set(range(len(vocab_list)))
    returned_ids = []

    for item in results:
        if not isinstance(item, dict):
            raise RuntimeError(
                "Gemini batch response contains a non-object item."
            )

        if "input_id" not in item:
            raise RuntimeError(
                "Gemini batch response contains an item without input_id."
            )

        returned_ids.append(item["input_id"])

    if len(results) != len(vocab_list):
        raise RuntimeError(
            "Gemini returned the wrong number of vocabulary items: "
            f"expected {len(vocab_list)}, got {len(results)}."
        )

    if set(returned_ids) != expected_ids or len(set(returned_ids)) != len(returned_ids):
        raise RuntimeError(
            "Gemini returned missing or duplicate input_id values."
        )

    results_by_id = {
        item["input_id"]: item
        for item in results
    }

    normalized = []

    for index, vocab in enumerate(vocab_list):
        result = results_by_id[index]

        word = str(result.get("word", "")).strip()
        reading = str(result.get("reading", "")).strip()
        example_sentence = str(
            result.get("example_sentence", "")
        ).strip()

        accepted_answers = [
            str(x).strip()
            for x in result.get("accepted_answers", [])
            if str(x).strip()
        ]

        semantic_variants = [
            str(x).strip()
            for x in result.get("semantic_variants", [])
            if str(x).strip()
        ]

        if not word:
            raise RuntimeError(
                f"Gemini did not provide a Japanese word for "
                f"{vocab['reading']}."
            )

        if not reading:
            raise RuntimeError(
                f"Gemini did not provide a reading for "
                f"{vocab['reading']}."
            )

        if not example_sentence:
            raise RuntimeError(
                f"Gemini did not provide an example sentence for "
                f"{vocab['reading']}."
            )

        if not accepted_answers:
            raise RuntimeError(
                f"Gemini did not provide accepted answers for "
                f"{vocab['reading']}."
            )

        normalized.append({
            "input_id": index,
            "word": word,
            "reading": reading,
            "accepted_answers": accepted_answers,
            "semantic_variants": semantic_variants,
            "example_sentence": example_sentence
        })

    return normalized


# ============================================================
# DATABASE HELPERS
# ============================================================

# ============================================================

def get_lesson_id(cur, lesson_number: int):
    row = cur.execute(
        """
        SELECT id
        FROM lessons
        WHERE lesson_number = ?
        """,
        (lesson_number,)
    ).fetchone()

    return row[0] if row else None


# ============================================================
# INSERT LESSONS
# ============================================================

def insert_lessons(cur):

    for lesson in LESSONS:

        cur.execute(
            """
            INSERT OR IGNORE INTO lessons
                (lesson_number, title)
            VALUES (?, ?)
            """,
            (
                lesson["lesson_number"],
                lesson["title"]
            )
        )

    print(f"✓ Lessons processed: {len(LESSONS)}")


# ============================================================
# INSERT KANJI
# ============================================================

def insert_kanji(cur):

    inserted = 0
    skipped = 0

    for item in KANJI_INPUT:

        lesson_id = get_lesson_id(
            cur,
            item["lesson_number"]
        )

        if lesson_id is None:

            print(
                f"⚠ Lesson {item['lesson_number']} "
                f"does not exist for kanji {item['character']}"
            )

            skipped += 1
            continue

        # Generate accepted answers from the information
        # supplied by the user.
        accepted_answers = [
            x.strip()
            for x in item["meaning"].split(";")
            if x.strip()
        ]

        cur.execute(
            """
            INSERT OR IGNORE INTO kanji
            (
                character,
                meaning,
                onyomi,
                kunyomi,
                jlpt_level,
                genki_lesson_id,
                accepted_answers
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["character"],
                item["meaning"],
                item.get("onyomi", ""),
                item.get("kunyomi", ""),
                item["jlpt_level"],
                lesson_id,
                ",".join(accepted_answers)
            )
        )

        if cur.rowcount > 0:
            inserted += 1

    print(f"✓ Kanji inserted: {inserted}")

    if skipped:
        print(f"⚠ Kanji skipped: {skipped}")


# ============================================================
# FIND EXISTING VOCABULARY
# ============================================================

def find_existing_vocabulary(
    cur,
    word: str,
    reading: str,
    lesson_id: int
):

    row = cur.execute(
        """
        SELECT id
        FROM vocabulary
        WHERE word = ?
          AND reading = ?
          AND genki_lesson_id = ?
        LIMIT 1
        """,
        (
            word,
            reading,
            lesson_id
        )
    ).fetchone()

    return row[0] if row else None


# ============================================================
# INSERT VOCABULARY
# ============================================================

def find_existing_vocabulary_by_source(
    cur,
    reading: str,
    meaning: str,
    lesson_id: int
):
    """
    Find an existing vocabulary record before calling Gemini.

    Reading + meaning + lesson are used together so that legitimate
    homophones are not accidentally treated as duplicates.
    """

    row = cur.execute(
        """
        SELECT id, word
        FROM vocabulary
        WHERE reading = ?
          AND meaning = ?
          AND genki_lesson_id = ?
        LIMIT 1
        """,
        (
            reading,
            meaning,
            lesson_id
        )
    ).fetchone()

    return row if row else None


def insert_vocabulary(cur):
    """
    Insert vocabulary using ONE Gemini request for all new vocabulary.

    Existing vocabulary is detected BEFORE Gemini enrichment, so rerunning
    this script does not waste Gemini tokens on records that already exist.
    """

    inserted = 0
    skipped = 0
    pending = []

    # ------------------------------------------------------------
    # Phase 1: resolve lessons and remove already-existing items
    # ------------------------------------------------------------

    for raw_vocab in VOCAB_INPUT:
        lesson_id = get_lesson_id(
            cur,
            raw_vocab["lesson_number"]
        )

        if lesson_id is None:
            print(
                f"⚠ Lesson {raw_vocab['lesson_number']} "
                f"does not exist for vocabulary "
                f"{raw_vocab['reading']}"
            )
            skipped += 1
            continue

        existing = find_existing_vocabulary_by_source(
            cur,
            raw_vocab["reading"],
            raw_vocab["meaning"],
            lesson_id
        )

        if existing is not None:
            print(
                f"  → Already exists: {existing[1]} "
                f"({raw_vocab['reading']})"
            )
            skipped += 1
            continue

        pending.append({
            "raw": raw_vocab,
            "lesson_id": lesson_id
        })

    # ------------------------------------------------------------
    # Phase 2: enrich ONLY new vocabulary in ONE Gemini request
    # ------------------------------------------------------------

    if not pending:
        print("\n✓ No new vocabulary requires Gemini enrichment.")
        print(f"✓ Vocabulary inserted: {inserted}")

        if skipped:
            print(
                f"⚠ Vocabulary skipped/existing: {skipped}"
            )

        return

    raw_items = [item["raw"] for item in pending]
    enriched_items = enrich_vocabulary_batch(raw_items)

    # ------------------------------------------------------------
    # Phase 3: insert the enriched records
    # ------------------------------------------------------------

    for pending_item, enriched in zip(pending, enriched_items):
        raw_vocab = pending_item["raw"]
        lesson_id = pending_item["lesson_id"]

        word = enriched["word"]
        reading = enriched["reading"]

        # User-provided curriculum fields are authoritative.
        meaning = raw_vocab["meaning"]
        jlpt_level = raw_vocab["jlpt_level"]
        part_of_speech = raw_vocab["part_of_speech"]

        accepted_answers = enriched["accepted_answers"]
        semantic_variants = enriched["semantic_variants"]
        example_sentence = enriched["example_sentence"]

        # --------------------------------------------------------
        # Safety duplicate check after enrichment
        # --------------------------------------------------------

        existing = find_existing_vocabulary(
            cur,
            word,
            reading,
            lesson_id
        )

        if existing is not None:
            print(
                f"  → Already exists after enrichment: {word}"
            )
            skipped += 1
            continue

        # --------------------------------------------------------
        # Insert
        # --------------------------------------------------------

        cur.execute(
            """
            INSERT INTO vocabulary
            (
                word,
                reading,
                meaning,
                jlpt_level,
                genki_lesson_id,
                part_of_speech,
                example_sentence,
                accepted_answers,
                semantic_variants
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                word,
                reading,
                meaning,
                jlpt_level,
                lesson_id,
                part_of_speech,
                example_sentence,
                json.dumps(
                    accepted_answers,
                    ensure_ascii=False
                ),
                json.dumps(
                    semantic_variants,
                    ensure_ascii=False
                )
            )
        )

        vocabulary_id = cur.lastrowid

        print(
            f"  ✓ Added: {word} "
            f"({reading})"
        )

        inserted += 1

        # --------------------------------------------------------
        # Automatically create kanji relationships
        # --------------------------------------------------------

        create_kanji_relationships(
            cur,
            word,
            vocabulary_id
        )

    print(
        f"\n✓ Vocabulary inserted: {inserted}"
    )

    if skipped:
        print(
            f"⚠ Vocabulary skipped/existing: {skipped}"
        )


# ============================================================
# AUTOMATIC KANJI ↔ VOCABULARY RELATIONSHIPS
# ============================================================

def create_kanji_relationships(
    cur,
    word: str,
    vocabulary_id: int
):
    """
    Looks at every character in the Japanese word.

    If that character exists in the kanji table,
    automatically creates the relationship.
    """

    for character in word:

        row = cur.execute(
            """
            SELECT id
            FROM kanji
            WHERE character = ?
            """,
            (character,)
        ).fetchone()

        if row is None:
            continue

        kanji_id = row[0]

        cur.execute(
            """
            INSERT OR IGNORE INTO kanji_vocabulary
            (
                kanji_id,
                vocabulary_id
            )
            VALUES (?, ?)
            """,
            (
                kanji_id,
                vocabulary_id
            )
        )

        print(
            f"    ↳ {character} → {word}"
        )


# ============================================================
# REBUILD ALL RELATIONSHIPS
# ============================================================

def rebuild_kanji_relationships(cur):

    """
    Useful if you add new kanji after vocabulary already exists.

    Example:

        First:
            料理 is inserted.

        Later:
            料 and 理 are inserted.

    Running this function will discover:

        料 → 料理
        理 → 料理
    """

    rows = cur.execute(
        """
        SELECT id, word
        FROM vocabulary
        """
    ).fetchall()

    relationship_count = 0

    for vocabulary_id, word in rows:

        before = cur.execute(
            """
            SELECT COUNT(*)
            FROM kanji_vocabulary
            WHERE vocabulary_id = ?
            """,
            (vocabulary_id,)
        ).fetchone()[0]

        create_kanji_relationships(
            cur,
            word,
            vocabulary_id
        )

        after = cur.execute(
            """
            SELECT COUNT(*)
            FROM kanji_vocabulary
            WHERE vocabulary_id = ?
            """,
            (vocabulary_id,)
        ).fetchone()[0]

        relationship_count += after - before

    print(
        f"✓ New kanji-vocabulary relationships: "
        f"{relationship_count}"
    )


# ============================================================
# DATABASE BUILD
# ============================================================

def build_database(path: str = DB_PATH):

    conn = sqlite3.connect(path)

    # Enable foreign keys
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # 1. Create tables
        # ----------------------------------------------------

        cur.executescript(SCHEMA)

        print("✓ Database schema ready")

        # ----------------------------------------------------
        # 2. Lessons
        # ----------------------------------------------------

        insert_lessons(cur)

        # ----------------------------------------------------
        # 3. Kanji
        # ----------------------------------------------------

        insert_kanji(cur)

        # ----------------------------------------------------
        # 4. Vocabulary
        # ----------------------------------------------------

        insert_vocabulary(cur)

        # ----------------------------------------------------
        # 5. Rebuild relationships
        # ----------------------------------------------------

        rebuild_kanji_relationships(cur)

        # ----------------------------------------------------
        # 6. Commit
        # ----------------------------------------------------

        conn.commit()

        print("\n====================================")
        print("DATABASE UPDATE COMPLETE")
        print("====================================")

    except Exception:

        conn.rollback()

        print(
            "\n❌ Error occurred."
            "\nDatabase changes have been rolled back."
        )

        raise

    finally:

        conn.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if not os.getenv("GOOGLE_API_KEY"):

        raise SystemExit(
            "ERROR: GOOGLE_API_KEY is missing.\n"
            "Add it to your .env file."
        )

    build_database()

    print(
        f"\nDatabase ready: {DB_PATH}"
    )