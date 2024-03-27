import json
from datetime import datetime
from typing import Callable

from beartype import beartype

import eventfully.database as db
from eventfully.logger import log
from eventfully.sources.ai_provider import chat_completion_request
from eventfully.sources.emails import get_emails
from eventfully.sources.zuerichunbezahlbar_ch import get_zuerichunbezahlbar

# Add new sources here
sources: list[Callable[[], list[db.RawEvent]]] = [
    get_emails,
    get_zuerichunbezahlbar,
]


def main():
    # Get the data from the sources
    raw_events: list[db.RawEvent] = []
    for source in sources:
        source_name = source.__name__

        log.debug(f"Getting data from source '{source_name}' ...")
        try:
            result = source()
        except Exception as e:
            log.warning(f"Error while getting data from '{source_name}'", exc_info=e)
            continue

        # Check if the result is a list of RawEvents
        if not (isinstance(result, list) and all(isinstance(i, db.RawEvent) for i in result)):
            log.error(f"'{source_name}' returned wrong type {type(result)}")
            continue

        raw_events += result

    # Clear duplicates
    exising_event_ids = db.get_existing_event_ids()
    new_raw_events = [
        event for event in raw_events if event.id not in exising_event_ids
    ]

    # Process the data with the AI provider
    new_events: list[db.Event] = []
    for raw_event in new_raw_events:
        try:
            new_event = process_raw_event(raw_event, "prompts.json")
        except Exception as e:
            log.warning(f"Error while processing event '{raw_event}'", exc_info=e)
            continue
        new_events.append(new_event)

    # Add the new events to the search database
    db.add_events(new_events)


@beartype
def process_raw_event(raw_event: db.RawEvent, prompts_path: str) -> db.Event:
    # Load attributes from the json file
    prompts: dict[str, str | dict[str, dict]] = json.load(open(prompts_path))

    filled_fields = {}
    for prompt_field_name, prompt_field_data in prompts["fields"].items():
        # Only get the description from the raw event if it's not empty to save tokens
        if prompt_field_name == "description" and raw_event.description:
            filled_fields[prompt_field_name] = raw_event.description
            continue

        # If the field in the raw event is already set only give it as context
        field_content = getattr(raw_event, prompt_field_name)
        if field_content:
            field = process_field(field_content, prompt_field_name, prompt_field_data, prompts["general"])
        else:
            field = process_field(raw_event, prompt_field_name, prompt_field_data, prompts["general"])

        # Convert date strings to time in seconds (e.g. 2024-02-25T13:30:00Z)
        if prompt_field_name in ["start_date", "end_date"]:
            field = int(datetime.strptime(field, "%Y-%m-%dT%H:%M:%SZ").timestamp())

        filled_fields[prompt_field_name] = field

    event = db.Event(**filled_fields)
    return event


@beartype
def process_field(
    context,
    field_name: str,
    field_data: dict[str, any],
    general_prompt: str,
) -> str | list[str]:
    messages = [
        {
            "role": "system",
            "content": general_prompt + "\n### Field Specification\n" + str(field_data["description"]) + "\n### Information\n" + str(field_data),
        },
        {"role": "user", "content": str(context)},
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": f"get_{field_name}",
                "description": f"Get {field_data['description']}",
                "parameters": {
                    "type": "object",
                    "properties": {field_name: field_data},
                    "required": [field_name],
                },
            },
        }
    ]

    completion = chat_completion_request(messages, tools)

    # Check if the AI has actually called the function
    if not completion.choices[0].message.tool_calls:

    result_field_json = completion.choices[0].message.tool_calls[0].function.arguments
    result_field = json.loads(result_field_json)
    return result_field[field_name]


if __name__ == "__main__":
    main()
