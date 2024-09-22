# prompt2map

**prompt2map** is a Python package that generates dynamic maps based on natural language prompts, utilizing Retrieval-Augmented Generation (RAG).

# Quickstart

## Initialize the mapper with geospatial data

To get started, initialize Prompt2Map by providing a geospatial data file, embeddings, and descriptions of the fields in your dataset:

```python
from prompt2map import Prompt2Map

# Example with portuguese 2021 Census
p2m = Prompt2Map.from_file(
    "censo2021portugal", 
    "data/censo_pt_2021/geodata.parquet",  # Main geospatial data source that will be queries and mapped 
    "data/censo_pt_2021/embeddings.parquet",  # Embedding for string literals
    "data/censo_pt_2021/variable_descriptions.csv" # Description of fields in geodata.parquet 
)
```

## Make a query

Once initialized, you can generate maps by making natural language queries. For example, to create a population density map:

```python
prompt = "Population density map of the district of Setúbal by parish in inhabitants / km2"
generated_map = p2m.to_map(prompt)
```

![Screenshot of a web choropleth map of Setúbal district with parish polygons](docs/images/example_map_censo_pt.png)