import geopandas as gpd
import pandas as pd
import pytest
from shapely import Point

from prompt2map.providers.geoduckdb import GeoDuckDB

db_data = [
    {
        'id': [1, 2, 3],
        'name': ['A', 'B', 'C'], 
        'geometry': [Point(i, i).buffer(0.1).envelope for i in range(1,4)]
    },
    {
        'id': [1, 2, 3],
        'field1': ['A', 'B', 'C'], 
        'field2': ['D', 'E', 'F'], 
        'geometry': [Point(i, i).buffer(0.1).envelope for i in range(1,4)]
    },
    {
        'id': [1, 2, 3, 4, 5],
        'name': ['A', 'B', 'C', 'D', 'E'], 
        'geometry': [Point(i, i).buffer(0.1).envelope for i in range(1,6)]
    }
]
lengths = [3, 3, 5]
tables = ["dataset", "dataset", "dataset"]
columns = ["geometry", "geometry", "geometry"]

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


@pytest.fixture
def db(tmp_path, request, embeddings_parquet, variable_descriptions_csv):
    geodata = gpd.GeoDataFrame(request.param, crs="EPSG:4326")
    geodata.to_parquet(tmp_path / "geodata.parquet", index=False)
    
    db = GeoDuckDB("dataset", 
        tmp_path / "geodata.parquet",
        embeddings_parquet,
        variable_descriptions_csv)
    
    return db

@pytest.mark.parametrize('db', db_data, indirect=["db"])
def test_get_schema(db):
    assert "CREATE TABLE dataset" in db.get_schema()

@pytest.mark.parametrize('db,table,column', list(zip(db_data, tables, columns)), indirect=["db"])
def test_get_geo_column(db, table, column):
    assert db.get_geo_column() == (table, column)

@pytest.mark.parametrize('db,db_length', list(zip(db_data, lengths)), indirect=["db"])
def test_get_geodata(db, db_length):
    gdf = db.get_geodata("SELECT * FROM dataset")
    assert len(gdf) == db_length
    assert gdf.crs == "EPSG:4326"
