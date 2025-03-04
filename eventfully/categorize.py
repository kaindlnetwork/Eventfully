from datetime import datetime
from functools import lru_cache
from json import loads
from os import getenv

import openai
from dotenv import load_dotenv

import eventfully.database as db

load_dotenv()
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("No OpenAI key provided. Please set OPENAI_API_KEY in .env file.")
openai.api_key = OPENAI_API_KEY


def categorize(text: str):
    time_format = "%d-%m-%Y %H:%M:%S"

    infos = loads(get_infos(text))
    tags = get_topic(text)

    print(infos["title"])
    event = db.Event(
        title=infos["title"],
        description=infos["description"],
        link=infos["link"],
        price=infos["price"],
        tags=[tags],
        start_date=datetime.strptime(infos["start_date"], time_format).timestamp(),
        end_date=datetime.strptime(infos["end_date"], time_format).timestamp(),
        age=infos["age"],
        accessibility=infos["accessibility"],
        address=infos["address"],
        city=infos["city"],
    )
    db.add_event(event)


@lru_cache
def get_infos(text: str) -> str:
    messages = [
        {
            "role": "system",
            "content": """Task: Extract the following event information's from the given text.
The output should be in the specifed form. Respond with "---" if you don't have enought information to fill a field.
You are allowed to shorten the output if you think it is necessary or too long.

Time Format: DD-MM-YYYY HH:MM:SS. Use 00:00:00 if you don't have the time.

Required Information:
- title
- description
- link
- price
- address
- city
- start date
- end date
- age
- accessibility

Output as JSON:
{
    "title": "..."
    "description": "..."
    "link": "..."
    "price": "..."
    "address": "...",
    "city": "...",
    "start_date": "..."
    "end_date": "..."
    "age": "..."
    "accessibility": "..."
}
"""
        },
        {
            "role": "user",
            "content": text
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5
    )
    return response["choices"][0]["message"]["content"]


@lru_cache
def get_topic(text: str) -> str:
    messages = [
        {
            "role": "system",
            "content": """Task: Classify the following Text by **ONE** of the following topics. Use the exact topic names that we give you. Don't make topics up on your own. 
 Topics:
 - MINT
 - Politik
 - Bürgerbeteiligung
 - Sprache
 - Handwerk
 - Informatik
 - Kunst/Kultur
 - Geschichte
 - Logikspiele/Spiele
 - Sport
 - Schule"""
        },
        {
            "role": "user",
            "content": "Bilderbuchgeschichten für Kinder ab 3 Jahren in der Stadtteilbibliothek Chorweiler"
        },
        {
            "role": "assistant",
            "content": "Sprache"
        },
        {
            "role": "user",
            "content": "Workshop Digitales Zeichnen"
        },
        {
            "role": "assistant",
            "content": "Informatik"
        },
        {
            "role": "user",
            "content": text
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return response["choices"][0]["message"]["content"]


def main():
    for email in db.EMailContent.select():
        categorize(email.subject + email.content)

    # db.EMailContent.delete().execute()

if __name__ == "__main__":
    main()
