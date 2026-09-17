import sqlite3


DB_PATH = "jlpt_agent.db"


# ============================================================
# 1. DATABASE SCHEMA
# ============================================================
#
# IMPORTANT:
# When adding a NEW TABLE in the future, simply add another
# CREATE TABLE IF NOT EXISTS block here.
#
# Do NOT use DROP TABLE.
#
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
    reading TEXT,
    meaning TEXT,
    jlpt_level TEXT,
    genki_lesson_id INTEGER REFERENCES lessons(id),
    part_of_speech TEXT,
    example_sentence TEXT,
    accepted_answers TEXT
);


CREATE TABLE IF NOT EXISTS kanji (
    id INTEGER PRIMARY KEY,
    character TEXT NOT NULL UNIQUE,
    meaning TEXT,
    onyomi TEXT,
    kunyomi TEXT,
    jlpt_level TEXT,
    genki_lesson_id INTEGER REFERENCES lessons(id),
    accepted_answers TEXT
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
# 2. LESSON DATA
# ============================================================
#
# Add future Genki lessons here.
#
# Example:
#
# (15, "Lesson 15 — ..."),
# (16, "Lesson 16 — ..."),
#
# Running the script again will NOT duplicate them.
#
# ============================================================

LESSONS = [

    (13, "Lesson 13 — Lending and Borrowing"),
    (14, "Lesson 14 — Comparison"),

    # Add future lessons here
    # (15, "Lesson 15 — ..."),
    # (16, "Lesson 16 — ..."),
]


# ============================================================
# 3. VOCABULARY DATA
# ============================================================
#
# Add new vocabulary here.
#
# Format:
#
# (
#     word,
#     reading,
#     meaning,
#     jlpt_level,
#     lesson_number,
#     part_of_speech,
#     example_sentence,
#     accepted_answers
# )
#
# ============================================================

VOCAB = [
  {
    "word": "おとな",
    "reading": "おとな",
    "meaning": "adult",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "adult"
    ]
  },
  {
    "word": "べんごし",
    "reading": "べんごし",
    "meaning": "lawyer",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "lawyer"
    ]
  },
  {
    "word": "わたくし",
    "reading": "わたくし",
    "meaning": "I (formal)",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "I",
      "formal I",
      "me"
    ]
  },
  {
    "word": "カレー",
    "reading": "カレー",
    "meaning": "curry",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "curry"
    ]
  },
  {
    "word": "こうちゃ",
    "reading": "こうちゃ",
    "meaning": "black tea",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "black tea",
      "tea"
    ]
  },
  {
    "word": "きもの",
    "reading": "きもの",
    "meaning": "kimono; Japanese traditional dress",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "kimono",
      "Japanese traditional dress"
    ]
  },
  {
    "word": "セーター",
    "reading": "セーター",
    "meaning": "sweater",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "sweater"
    ]
  },
  {
    "word": "がっき",
    "reading": "がっき",
    "meaning": "musical instrument",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "musical instrument",
      "instrument"
    ]
  },
  {
    "word": "からて",
    "reading": "からて",
    "meaning": "karate",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "karate"
    ]
  },
  {
    "word": "ゴルフ",
    "reading": "ゴルフ",
    "meaning": "golf",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "golf"
    ]
  },
  {
    "word": "バイク",
    "reading": "バイク",
    "meaning": "motorcycle",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "motorcycle",
      "motorbike"
    ]
  },
  {
    "word": "ぞう",
    "reading": "ぞう",
    "meaning": "elephant",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "elephant"
    ]
  },
  {
    "word": "からだ",
    "reading": "からだ",
    "meaning": "body",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "body"
    ]
  },
  {
    "word": "がいこくご",
    "reading": "がいこくご",
    "meaning": "foreign language",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "foreign language"
    ]
  },
  {
    "word": "ことば",
    "reading": "ことば",
    "meaning": "language",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "language"
    ]
  },
  {
    "word": "ぶんぽう",
    "reading": "ぶんぽう",
    "meaning": "grammar",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "grammar"
    ]
  },
  {
    "word": "アプリ",
    "reading": "アプリ",
    "meaning": "application",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "application",
      "app"
    ]
  },
  {
    "word": "アパート",
    "reading": "アパート",
    "meaning": "apartment; smaller apartment",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "apartment",
      "small apartment"
    ]
  },
  {
    "word": "マンション",
    "reading": "マンション",
    "meaning": "larger apartment building; condominium",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "apartment building",
      "larger apartment building",
      "condominium",
      "condo"
    ]
  },
  {
    "word": "くうこう",
    "reading": "くうこう",
    "meaning": "airport",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "airport"
    ]
  },
  {
    "word": "みせ",
    "reading": "みせ",
    "meaning": "shop; store",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "shop",
      "store"
    ]
  },
  {
    "word": "ぶっか",
    "reading": "ぶっか",
    "meaning": "consumer prices",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "consumer prices",
      "prices"
    ]
  },
  {
    "word": "こうこく",
    "reading": "こうこく",
    "meaning": "advertisement",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "advertisement",
      "advertising",
      "ad"
    ]
  },
  {
    "word": "ぼしゅう",
    "reading": "ぼしゅう",
    "meaning": "recruitment",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "recruitment",
      "recruiting"
    ]
  },
  {
    "word": "やくそく",
    "reading": "やくそく",
    "meaning": "promise; appointment",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "noun",
    "example_sentence": "",
    "accepted_answers": [
      "promise",
      "appointment"
    ]
  },
  {
    "word": "うれしい",
    "reading": "うれしい",
    "meaning": "glad",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "i-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "glad",
      "happy"
    ]
  },
  {
    "word": "かなしい",
    "reading": "かなしい",
    "meaning": "sad",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "i-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "sad"
    ]
  },
  {
    "word": "きびしい",
    "reading": "きびしい",
    "meaning": "strict",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "i-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "strict"
    ]
  },
  {
    "word": "きぶんがわるい",
    "reading": "きぶんがわるい",
    "meaning": "to feel sick",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "i-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "to feel sick",
      "feel sick",
      "feel ill"
    ]
  },
  {
    "word": "からい",
    "reading": "からい",
    "meaning": "hot and spicy; salty",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "i-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "hot and spicy",
      "spicy",
      "salty"
    ]
  },
  {
    "word": "すごい",
    "reading": "すごい",
    "meaning": "incredible; awesome",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "i-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "incredible",
      "awesome"
    ]
  },
  {
    "word": "ちかい",
    "reading": "ちかい",
    "meaning": "close; near",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "i-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "close",
      "near"
    ]
  },
  {
    "word": "いろいろ（な）",
    "reading": "いろいろ（な）",
    "meaning": "various; different kinds of",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "na-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "various",
      "different kinds of"
    ]
  },
  {
    "word": "しあわせ（な）",
    "reading": "しあわせ（な）",
    "meaning": "happy (lasting happiness)",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "na-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "happy",
      "happiness"
    ]
  },
  {
    "word": "だめ（な）",
    "reading": "だめ（な）",
    "meaning": "no good",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "na-adjective",
    "example_sentence": "",
    "accepted_answers": [
      "no good",
      "not good"
    ]
  },
  {
    "word": "おむ",
    "reading": "おむ",
    "meaning": "to knit",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "u-verb",
    "example_sentence": "",
    "accepted_answers": [
      "to knit",
      "knit"
    ]
  },
  {
    "word": "がんばる",
    "reading": "がんばる",
    "meaning": "to do one's best; to try hard",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "u-verb",
    "example_sentence": "",
    "accepted_answers": [
      "to do one's best",
      "to try hard",
      "try hard",
      "do one's best"
    ]
  },
  {
    "word": "なく",
    "reading": "なく",
    "meaning": "to cry",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "u-verb",
    "example_sentence": "",
    "accepted_answers": [
      "to cry",
      "cry"
    ]
  },
  {
    "word": "みがく",
    "reading": "みがく",
    "meaning": "to brush (teeth); to polish",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "u-verb",
    "example_sentence": "",
    "accepted_answers": [
      "to brush teeth",
      "brush teeth",
      "to polish",
      "polish"
    ]
  },
  {
    "word": "やくそくをまもる",
    "reading": "やくそくをまもる",
    "meaning": "to keep a promise",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "u-verb",
    "example_sentence": "",
    "accepted_answers": [
      "to keep a promise",
      "keep a promise"
    ]
  },
  {
    "word": "かんどうする",
    "reading": "かんどうする",
    "meaning": "to be moved; to be touched",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "irregular verb",
    "example_sentence": "",
    "accepted_answers": [
      "to be moved",
      "to be touched",
      "moved",
      "touched"
    ]
  },
  {
    "word": "～かい",
    "reading": "～かい",
    "meaning": "... times",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "expression",
    "example_sentence": "",
    "accepted_answers": [
      "times"
    ]
  },
  {
    "word": "～キロ",
    "reading": "～キロ",
    "meaning": "... kilometers; ... kilograms",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "expression",
    "example_sentence": "",
    "accepted_answers": [
      "kilometers",
      "kilograms",
      "kilometer",
      "kilogram"
    ]
  },
  {
    "word": "ぜんぶ",
    "reading": "ぜんぶ",
    "meaning": "all",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "adverb",
    "example_sentence": "",
    "accepted_answers": [
      "all"
    ]
  },
  {
    "word": "～ともうします",
    "reading": "～ともうします",
    "meaning": "my name is ...",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "expression",
    "example_sentence": "",
    "accepted_answers": [
      "my name is",
      "my name is ..."
    ]
  },
  {
    "word": "とくに",
    "reading": "とくに",
    "meaning": "especially",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "adverb",
    "example_sentence": "",
    "accepted_answers": [
      "especially"
    ]
  },
  {
    "word": "いちにち",
    "reading": "いちにち",
    "meaning": "one day",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "one day"
    ]
  },
  {
    "word": "ふつか",
    "reading": "ふつか",
    "meaning": "two days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "two days"
    ]
  },
  {
    "word": "みっか",
    "reading": "みっか",
    "meaning": "three days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "three days"
    ]
  },
  {
    "word": "よっか",
    "reading": "よっか",
    "meaning": "four days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "four days"
    ]
  },
  {
    "word": "いつか",
    "reading": "いつか",
    "meaning": "five days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "five days"
    ]
  },
  {
    "word": "むいか",
    "reading": "むいか",
    "meaning": "six days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "six days"
    ]
  },
  {
    "word": "なのか",
    "reading": "なのか",
    "meaning": "seven days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "seven days"
    ]
  },
  {
    "word": "ようか",
    "reading": "ようか",
    "meaning": "eight days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "eight days"
    ]
  },
  {
    "word": "ここのか",
    "reading": "ここのか",
    "meaning": "nine days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "nine days"
    ]
  },
  {
    "word": "とおか",
    "reading": "とおか",
    "meaning": "ten days",
    "jlpt_level": "N4",
    "lesson_number": 13,
    "part_of_speech": "number/counter",
    "example_sentence": "",
    "accepted_answers": [
      "ten days"
    ]
  }
]


# ============================================================
# 4. KANJI DATA
# ============================================================
#
# Format:
#
# (
#     character,
#     meaning,
#     onyomi,
#     kunyomi,
#     jlpt_level,
#     lesson_number,
#     accepted_answers
# )
#
# ============================================================

KANJI = [

    (
        "貸",
        "lend",
        "タイ",
        "か.す",
        "N4",
        13,
        "lend,to lend",
    ),

    (
        "借",
        "borrow",
        "シャク",
        "か.りる",
        "N4",
        13,
        "borrow,to borrow",
    ),

    (
        "京",
        "capital",
        "キョウ、ケイ",
        "みやこ",
        "N5",
        13,
        "capital,capital city",
    ),

    (
        "経",
        "experience/pass through",
        "ケイ",
        "へ.る",
        "N4",
        14,
        "experience,pass through",
    ),

    (
        "験",
        "test/effect",
        "ケン",
        "",
        "N4",
        14,
        "test,effect,trial",
    ),

    # ========================================================
    # ADD FUTURE KANJI HERE
    # ========================================================

]


# ============================================================
# 5. KANJI ↔ VOCABULARY RELATIONSHIPS
# ============================================================
#
# Example:
#
# "貸": ["貸す"]
#
# means:
#
# 貸 is used in 貸す
#
# ============================================================

KANJI_VOCAB_LINKS = {

    "物": [
        "食べ物",
        "物",
        "買い物"
    ],

    "鳥": [
        "鳥"
    ],

    "料": [
        "料理"
    ],

    "理": [
        "料理"
    ],

    "特": [
        "特に"
    ],

    "安": [
        "安い"
    ],

    "飯": [
        "ご飯",
        "朝ご飯",
        "昼ご飯"
    ],

    "肉": [
        "肉"
    ],

    "悪": [
        "悪い",
        "気分が悪い"
    ],

    "体": [
        "体"
    ],

    "同": [
        "同じ"
    ],

    "着": [
        "着く",
        "着る",
        "着物"
    ],

    "空": [
        "空港",
        "空気"
    ],

    "港": [
        "空港"
    ],

    "昼": [
        "昼",
        "昼ご飯"
    ],

    "海": [
        "海"
    ]
}

# ============================================================
# 6. GRAMMAR DATA
# ============================================================
#
# Format:
#
# (
#     pattern,
#     meaning,
#     formation,
#     jlpt_level,
#     lesson_number,
#     usage_notes,
#     common_mistakes,
#     accepted_answers
# )
#
# ============================================================

GRAMMAR = [

    (
        "～てあげる",
        "to do something for someone (as a favor)",
        "Verb-te + あげる",
        "N4",
        13,
        "Used when the speaker does a favor for someone else. "
        "Can sound condescending toward superiors — use ～てさしあげる "
        "or avoid it there.",
        "Using てあげる toward a teacher/boss without care can sound rude.",
        "do a favor,do something for,favor for someone",
    ),

    (
        "～のほうが～より",
        "X is more ~ than Y",
        "Noun A のほうが Noun B より Adjective",
        "N4",
        14,
        "Standard comparison structure in Japanese.",
        "Forgetting のほうが and just using より alone changes emphasis.",
        "more than,is more than,comparison",
    ),

    # ========================================================
    # ADD FUTURE GRAMMAR HERE
    # ========================================================

]


# ============================================================
# 7. BUILD DATABASE
# ============================================================

def build_database(path: str = DB_PATH) -> None:

    conn = sqlite3.connect(path)

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # Create tables
        # ----------------------------------------------------

        cur.executescript(SCHEMA)

        # ----------------------------------------------------
        # Insert lessons
        # ----------------------------------------------------

        cur.executemany(
            """
            INSERT OR IGNORE INTO lessons
                (lesson_number, title)
            VALUES (?, ?)
            """,
            LESSONS,
        )

        # Get lesson IDs
        lesson_id_by_number = {
            row[0]: row[1]
            for row in cur.execute(
                "SELECT lesson_number, id FROM lessons"
            )
        }

        # ----------------------------------------------------
        # Insert vocabulary
        # ----------------------------------------------------

        for (
            word,
            reading,
            meaning,
            level,
            lesson_num,
            pos,
            example,
            accepted,
        ) in VOCAB:

            lesson_id = lesson_id_by_number.get(lesson_num)

            if lesson_id is None:
                print(
                    f"WARNING: Lesson {lesson_num} does not exist. "
                    f"Skipping vocabulary: {word}"
                )
                continue

            cur.execute(
                """
                INSERT OR IGNORE INTO vocabulary
                (
                    word,
                    reading,
                    meaning,
                    jlpt_level,
                    genki_lesson_id,
                    part_of_speech,
                    example_sentence,
                    accepted_answers
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    word,
                    reading,
                    meaning,
                    level,
                    lesson_id,
                    pos,
                    example,
                    accepted,
                ),
            )

        # ----------------------------------------------------
        # Create vocabulary lookup
        # ----------------------------------------------------

        vocab_id_by_word = {
            row[0]: row[1]
            for row in cur.execute(
                "SELECT word, id FROM vocabulary"
            )
        }

        # ----------------------------------------------------
        # Insert kanji
        # ----------------------------------------------------

        for (
            char,
            meaning,
            onyomi,
            kunyomi,
            level,
            lesson_num,
            accepted,
        ) in KANJI:

            lesson_id = lesson_id_by_number.get(lesson_num)

            if lesson_id is None:
                print(
                    f"WARNING: Lesson {lesson_num} does not exist. "
                    f"Skipping kanji: {char}"
                )
                continue

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
                    char,
                    meaning,
                    onyomi,
                    kunyomi,
                    level,
                    lesson_id,
                    accepted,
                ),
            )

        # ----------------------------------------------------
        # Create kanji lookup
        # ----------------------------------------------------

        kanji_id_by_char = {
            row[0]: row[1]
            for row in cur.execute(
                "SELECT character, id FROM kanji"
            )
        }

        # ----------------------------------------------------
        # Insert Kanji ↔ Vocabulary relationships
        # ----------------------------------------------------

        for char, words in KANJI_VOCAB_LINKS.items():

            kanji_id = kanji_id_by_char.get(char)

            if kanji_id is None:
                print(
                    f"WARNING: Kanji {char} does not exist. "
                    f"Skipping relationship."
                )
                continue

            for word in words:

                vocabulary_id = vocab_id_by_word.get(word)

                if vocabulary_id is None:
                    print(
                        f"WARNING: Vocabulary {word} does not exist. "
                        f"Skipping relationship."
                    )
                    continue

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
                        vocabulary_id,
                    ),
                )

        # ----------------------------------------------------
        # Insert grammar
        # ----------------------------------------------------

        for (
            pattern,
            meaning,
            formation,
            level,
            lesson_num,
            notes,
            mistakes,
            accepted,
        ) in GRAMMAR:

            lesson_id = lesson_id_by_number.get(lesson_num)

            if lesson_id is None:
                print(
                    f"WARNING: Lesson {lesson_num} does not exist. "
                    f"Skipping grammar: {pattern}"
                )
                continue

            cur.execute(
                """
                INSERT OR IGNORE INTO grammar
                (
                    pattern,
                    meaning,
                    formation,
                    jlpt_level,
                    genki_lesson_id,
                    usage_notes,
                    common_mistakes,
                    accepted_answers
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pattern,
                    meaning,
                    formation,
                    level,
                    lesson_id,
                    notes,
                    mistakes,
                    accepted,
                ),
            )

        # ----------------------------------------------------
        # Commit everything
        # ----------------------------------------------------

        conn.commit()

        print("Database updated successfully.")

    except Exception:

        # If something goes wrong, undo the transaction.
        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# 8. RUN
# ============================================================

if __name__ == "__main__":
    build_database()
    print(f"Database ready: {DB_PATH}")
