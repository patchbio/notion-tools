# notion-tools

Python tools to work with the Notion API, including retrieving databases as
Pandas dataframes.

See DEVELOP.md for information on testing/docs.

## Getting Started

```shell
pip install notion-tools
```

Depends on [`pandas`](https://pandas.pydata.org/) and
[`notion-client`](https://github.com/ramnes/notion-sdk-py).

## Usage

```python
from notion_tools import get_notion_token, get_notion_client, database_to_dataframe

database_id = # database id retrievable from the share URL
notion_client = get_notion_client(get_notion_token())
df = database_to_dataframe(notion_client, database_id)
```

To find the database id, take the hex string from the URL for sharing the page:

```
https://www.notion.so/yourworkspace/{database_id}?v={other_hex_stuff}
```

## API

```
notion_tools.get_notion_token() -> str

   Gets a Notion API token.

   Either from the NOTION_TOKEN environment variable or interactively.

   Returns:
      The Notion API token.

   Return type:
      str

notion_tools.get_notion_client(token: Optional[str] = None) -> notion_client.client.Client

   Gets a Notion API client.

   The Notion API client used is https://github.com/ramnes/notion-sdk-
   py

   Parameters:
      **token** -- The Notion API Integration Token.

   Returns:
      The Notion API client.

   Return type:
      NotionClient

notion_tools.nonpaginated(endpoint, wait=0.1)

   Create a non-paginated version of a Notion endpoint.

   Wraps a paginated Notion endpoint and when called, will return a
   response object that concats all the pages. Waits *wait* seconds on
   each iteration to the API.

   -[ Example ]-

   response =
   nonpaginated(notion_client.blocks.children.list)(block_id)
   >>``<<>>`<<

notion_tools.database_to_dataframe(notion_client: notion_client.client.Client, database_id: str, default_date_handler: str = 'ignore_end', date_handlers: Optional[dict] = None) -> pandas.core.frame.DataFrame

   Extracts a Notion Database as a Pandas DataFrame.

   Parameters:
      * **notion_client** -- The Notion API client.

      * **database_id** -- The Notion Database ID. This identifier can
        be found in the URL of the database.

      * **default_date_handler** (*{"ignore_end"**, **"mangle"**,
        **"multiindex"}*) -- The default date handler. See Notes below
        on how to use this.

      * **date_handlers** -- Specify per-column date handlers.

   Returns:
      The Notion Database as a Pandas DataFrame.

   Return type:
      pd.DataFrame

   -[ Notes ]-

   Notion date properties are represented as 2-tuples with a start and
   end timestamps. If there is only a single date in the property, it
   is encoded as a start date with a null end date. There are several
   options on how to encode this into the resulting dataframe.

   "ignore_end":
      Keep only the start date of the date object and keep column name
      the same as the property name.

   "mangle":
      For each date property named "foo" in the Notion table, create a
      "foo_start" and a "foo_end" column.

   "multiindex":
      Create a MultiIndex for the columns where the top level contains
      the property names and the second level contains "start" and
      "end" for date properties.

notion_tools.users_to_dataframe(notion_client: notion_client.client.Client)

   Extract all Notion users as a Pandas DataFrame.

   Parameters:
      **notion_client** -- The Notion API client.

   Returns:
      The Notion users as a Pandas DataFrame.

   Return type:
      pd.DataFrame

   -[ Notes ]-

   If users are deleted from your Notion workspace, they will not be
   returned by the API, even if they are still present in Person
   properties in your databases.
```
