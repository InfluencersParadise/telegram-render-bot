import os
import json
import re
import asyncio
from typing import Optional, Dict, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import aiosqlite

BOT_TOKEN = os.getenv("AAFHkUeocq0Cwk35kR8XuZfgPx1BDdmmmPo")
DB_PATH = "stats.db"

TOPIC_RULES: Dict[str, Tuple[str, ...]] = {
    "Support": ("hilfe", "problem", "bug", "error", "geht nicht"),
    "Ankündigungen": ("ankündigung", "update", "release", "neu"),
    "Offtopic": ("meme", "witz", "funny"),
    "Tech": ("python", "server", "cloud", "docker"),
    "Sonstiges": ()
}

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())

def classify_topic(text: Optional[str]) -> str:
    if not text:
        return "Sonstiges"
    t = normalize(text)
    for topic, kws in TOPIC_RULES.items():
        if topic == "Sonstiges":
            continue
        for kw in kws:
            if kw in t:
                return topic
    return "Sonstiges"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS user_stats (
  chat_id INTEGER,
  user_id INTEGER,
  user_name TEXT,
  msg_count INTEGER DEFAULT 0,
  image_count INTEGER DEFAULT 0,
  topic_json TEXT DEFAULT '{}',
  PRIMARY KEY (chat_id, user_id)
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_SQL)
        await db.commit()

async def update_stats(chat_id, user_id, name, is_photo, topic):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT msg_count, image_count, topic_json FROM user_stats WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()

        if row:
            msg, img, tj = row
            topics = json.loads(tj)
        else:
            msg, img, topics = 0, 0, {}

        msg += 1
        if is_photo:
            img += 1

        topics[topic] = topics.get(topic, 0) + 1

        await db.execute(
            "REPLACE INTO user_stats VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, user_id, name, msg, img, json.dumps(topics)),
        )
        await db.commit()

dp = Dispatcher()

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_msg(message: Message):
    if not message.from_user:
        return

    topic = classify_topic(message.text or message.caption)
    await update_stats(
        message.chat.id,
        message.from_user.id,
        message.from_user.full_name,
        bool(message.photo),
        topic,
    )

@dp.message(F.text == "/top")
async def top(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_name, msg_count FROM user_stats WHERE chat_id=? ORDER BY msg_count DESC LIMIT 10",
            (message.chat.id,),
        )
        rows = await cur.fetchall()

    txt = "Top User nach Nachrichten:\n"
    for i, (name, count) in enumerate(rows, 1):
        txt += f"{i}. {name}: {count}\n"

    await message.reply(txt)

async def main():
    await init_db()
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)

asyncio.run(main())