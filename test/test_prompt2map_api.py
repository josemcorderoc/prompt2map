import os
from typing import Optional

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from prompt2map.application.core.prompt2map import Prompt2Map
from prompt2map.providers.openai import OpenAIProvider
from prompt2map.types import Map


@pytest.fixture
def geodata_parquet(tmp_path):
    # Generate 5 rows of test data with polygons and add a CRS
    data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['A', 'B', 'C', 'D', 'E'],
        'geometry': [
            Point(1, 1).buffer(0.1).envelope, 
            Point(2, 2).buffer(0.1).envelope, 
            Point(3, 3).buffer(0.1).envelope, 
            Point(4, 4).buffer(0.1).envelope, 
            Point(5, 5).buffer(0.1).envelope
        ]
    }
    geodata = gpd.GeoDataFrame(data, crs="EPSG:4326")
    geodata.to_parquet(tmp_path / "geodata.parquet", index=False)
    return tmp_path / "geodata.parquet"

@pytest.fixture
def embeddings_parquet(tmp_path):
    data = {
        'text': ["A", "B", "C", "D", "E"],
        'values': [
            [1, 2, 3, 4, 5],
            [2, 3, 4, 5, 6],
            [3, 4, 5, 6, 7],
            [4, 5, 6, 7, 8],
            [5, 6, 7, 8, 9]
        ]
    }
    embeddings = pd.DataFrame(data)
    embeddings.to_parquet(tmp_path / "embeddings.parquet", index=False)
    return tmp_path / "embeddings.parquet"

@pytest.fixture
def variable_descriptions_csv(tmp_path):
    data = {
        'column': ['A', 'B', 'C', 'D', 'E'],
        'description': ['Description A', 'Description B', 'Description C', 'Description D', 'Description E']
    }
    descriptions = pd.DataFrame(data)
    descriptions.to_csv(tmp_path / "variable_descriptions.csv", index=False)
    return tmp_path / "variable_descriptions.csv"

def dummy_generate_map(self, prompt: str, data: gpd.GeoDataFrame) -> Optional[Map]:
    return data.explore()
    

def test_prompt2map_from_file(mocker, geodata_parquet, embeddings_parquet, variable_descriptions_csv):
    # mocks
    mocker.patch('prompt2map.application.generators.openai_map_generator.OpenAIMapGenerator.generate', dummy_generate_map)
    mocker.patch.object(OpenAIProvider, "__init__", lambda x: None)
    
    geodf = gpd.read_parquet(geodata_parquet)
    mocker.patch('prompt2map.application.retrievers.sql_geo_retriever.SQLGeoRetriever.retrieve', return_value=geodf)

    p2m = Prompt2Map.from_file(
        "dataset", 
        geodata_parquet,
        embeddings_parquet,
        variable_descriptions_csv)

    query = "Population density map of the district of Setúbal by parish in inhabitants / km2"
    m = p2m.to_map(query)
