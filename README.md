# notion-tools

Python tools to work with the Notion API, including retrieving databases as
Pandas dataframes.

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

## API

TODO
