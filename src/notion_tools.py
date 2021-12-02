from __future__ import annotations

import os
from getpass import getpass
from time import sleep

import pandas as pd
from notion_client import Client as NotionClient


def get_notion_token() -> str:
    """Gets a Notion API token.

    Either from the NOTION_TOKEN environment variable or interactively.

    Returns
    -------
    str
        The Notion API token.
    """
    if "NOTION_TOKEN" in os.environ:
        return os.environ["NOTION_TOKEN"]
    else:
        return getpass("Enter Notion API Integration Token: ")


def get_notion_client(token: str) -> NotionClient:
    """Gets a Notion API client.

    The Notion API client used is
    https://github.com/ramnes/notion-sdk-py

    Parameters
    ----------
    token
        The Notion API Integration Token.

    Returns
    -------
    NotionClient
        The Notion API client.
    """
    return NotionClient(auth=token)


def _simplify_notion_property_value(value: dict):
    """Convert Notion Property Value to a simple/primitive data type

    Note that "date" types return a 2-tuple of (start, end) Timestamps.
    """
    type_ = value["type"]
    obj = value[type_]

    if obj is None:
        return obj
    elif type_ == "url":
        return obj
    elif type_ == "email":
        return obj
    elif type_ == "phone_number":
        return obj
    elif type_ == "number":
        return obj
    elif type_ == "created_time":
        return obj
    elif type_ == "last_edited_time":
        return obj
    elif type_ == "relation":
        # extract the IDs of the relation (linked page)
        return [v["id"] for v in obj]
    elif type_ == "checkbox":
        return bool(obj)
    elif type_ == "date":
        return (pd.Timestamp(obj["start"]), pd.Timestamp(obj["end"]))
    elif type_ == "created_by":
        return obj["name"]
    elif type_ == "last_edited_by":
        return obj.get("name")
    elif type_ == "select":
        return obj["name"]
    elif type_ == "multi_select":
        return [x["name"] for x in obj]
    elif type_ == "people":
        return [x["name"] for x in obj if "name" in x]
    elif type_ == "files":
        return [x[x["type"]]["url"] for x in obj]
    elif type_ == "title":
        return " ".join([x["plain_text"].strip() for x in obj])
    elif type_ == "rich_text":
        return " ".join([x["plain_text"].strip() for x in obj])
    elif type_ == "formula":
        return obj[obj["type"]]
    elif type_ == "rollup":
        if obj["type"] == "array":
            return [_simplify_notion_property_value(x) for x in obj["array"]]
        else:
            return obj[obj["type"]]
    else:
        raise ValueError(f"I don't understand type {type_}")


def _page_to_simple_dict(
    page: dict,
    default_date_handler: str = "ignore_end",
    date_handlers: dict[str, str] = None,
) -> dict:
    """Convert Notion Page objects to a "simple" dictionary suitable for Pandas.

    This is suitable for objects that have `"object": "page"`

    """
    if date_handlers is None:
        date_handlers = {}
    # these properties are defined by Notion
    record = {
        "_notion_id": page["id"],
        "_created_time": pd.Timestamp(page["created_time"]),
        "_last_edited_time": pd.Timestamp(page["last_edited_time"]),
        "_notion_url": page["url"],
    }
    for property, value in page["properties"].items():
        extracted = _simplify_notion_property_value(value)
        if value["type"] == "date":
            handler = date_handlers.get(property, default_date_handler)
            if handler == "ignore_end":
                record[property] = extracted[0]
            elif handler == "mangle":
                record[f"{property}_start"] = extracted[0]
                record[f"{property}_end"] = extracted[1]
            elif handler == "multiindex":
                record[(property, "start")] = extracted[0]
                record[(property, "end")] = extracted[1]
        else:
            record[property] = extracted
    return record


def database_to_dataframe(
    notion_client: NotionClient,
    database_id: str,
    default_date_handler: str = "ignore_end",
    date_handlers: dict[str, str] = None,
) -> pd.DataFrame:
    """Extracts a Notion Database as a Pandas DataFrame.

    Parameters
    ----------
    notion_client
        The Notion API client.
    database_id
        The Notion Database ID. This identifier can be found in the URL of the
        database.
    default_date_handler : {"ignore_end", "mangle", "multiindex"}
        The default date handler. See Notes below on how to use this.
    date_handlers
        Specify per-column date handlers.

    Returns
    -------
    pd.DataFrame
        The Notion Database as a Pandas DataFrame.

    Notes
    -----
    Notion date properties are represented as 2-tuples with a start and end
    timestamps. If there is only a single date in the property, it is encoded as
    a start date with a null end date. There are several options on how to
    encode this into the resulting dataframe.

    "ignore_end":
        Keep only the start date of the date object and keep column name the
        same as the property name.
    "mangle":
        For each date property named "foo" in the Notion table, create a
        "foo_start" and a "foo_end" column.
    "multiindex":
        Create a MultiIndex for the columns where the top level contains the
        property names and the second level contains "start" and "end" for
        date properties.
    """
    # accumulate all the pages in the database
    response = notion_client.databases.query(database_id)
    results = response["results"]
    while response["has_more"]:
        sleep(0.1)
        response = notion_client.databases.query(
            database_id, start_cursor=response["next_cursor"]
        )
        results += response["results"]

    # convert each page to a simplified dict => Pandas DataFrame
    records = map(
        lambda page: _page_to_simple_dict(
            page,
            default_date_handler=default_date_handler,
            date_handlers=date_handlers,
        ),
        results,
    )
    df = pd.DataFrame(records)

    # if any of the columns are tuples, it means those were date columns which
    # were handled with "multiindex" => the dataframe needs to be given
    # hierarchical columns
    if any(isinstance(col, tuple) for col in df.columns):
        multiindex = pd.MultiIndex.from_tuples(
            [col if isinstance(col, tuple) else (col, "") for col in df.columns]
        )
        df.columns = multiindex

    return df


def _user_to_simple_dict(user: dict) -> dict:
    """Convert Notion User objects to a "simple" dictionary suitable for Pandas.

    This is suitable for objects that have `"object": "user"`
    """
    record = {
        "notion_id": user["id"],
        "type": user["type"],
        "name": user["name"],
        "avatar_url": user["avatar_url"],
    }
    if user["type"] == "person":
        record["email"] = user["person"]["email"]
    return record


def users_to_dataframe(notion_client: NotionClient):
    """Extract all Notion users as a Pandas DataFrame.

    Parameters
    ----------
    notion_client
        The Notion API client.

    Returns
    -------
    pd.DataFrame
        The Notion users as a Pandas DataFrame.

    Notes
    -----
    If users are deleted from your Notion workspace, they will not be returned
    by the API, even if they are still present in Person properties in your
    databases.
    """
    response = notion_client.users.list()
    results = response["results"]
    while response["has_more"]:
        sleep(0.1)
        response = notion_client.users.list(start_cursor=response["next_cursor"])
        results += response["results"]
    return pd.DataFrame(map(_user_to_simple_dict, results))
