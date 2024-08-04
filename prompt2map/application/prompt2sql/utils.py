from bidict import bidict
import numpy as np
from sqlglot import parse_one, exp


def is_read_only_query(query: str) -> bool:
    parsed_query = parse_one(query)
    if parsed_query is None:
            raise ValueError(f"Query {query} could not be parsed.")
    expression = parsed_query.find(exp.Insert, exp.Update, exp.Delete)
    return expression is None


def to_geospatial_query(query: str, geospatial_columns: dict[str, str]) -> str:
    parsed_query = parse_one(query)
    table_alias = bidict({t.alias:t.name for t in parsed_query.find_all(exp.Table)})
    table_names = [t.name for t in parsed_query.find_all(exp.Table)]
    
    if parsed_query is None:
        raise ValueError(f"Query {query} could not be parsed.")
    
    for col in geospatial_columns:
        if col not in table_names:
            raise ValueError(f"Geotable {col} not found in query.")

    
    select = parsed_query.find(exp.Select)
    group_by = parsed_query.find(exp.Group)
    
    if select is None:
        raise ValueError(f"Query {query} does not contain a SELECT clause.")
    
    # if select contains comuna, add geom
    # geospatial_exp = [e for e in select.expressions if type(e) == exp.Column and table_alias[e.table] in geospatial_columns.keys()]
    
    
    if len(set(table_names).intersection(set(geospatial_columns.keys()))) > 0 and group_by is None:
        new_column = exp.Column(this=exp.Identifier(this="geom"))
        # if geospatial_exp[0].table != "":
        #     new_column = exp.Column(this=exp.Identifier(this=geospatial_columns[table_alias[geospatial_exp[0].table]]), table=exp.Identifier(this=geospatial_exp[0].table))
        select.expressions.append(new_column)   
    elif group_by is not None:
        group_by_tables = [table_alias[e.table] for e in group_by.expressions if type(e) == exp.Column and e.table in table_alias and table_alias[e.table] not in geospatial_columns.keys()]
        for geotable, geocol in geospatial_columns.items():
            if geotable not in group_by_tables:
                # aggregation = exp.Anonymous(func=exp.Identifier(this="ST_Union"), args=[exp.Column(this=exp.Identifier(this=geocol))])
                # select.expressions.append(aggregation)
                
                if geotable in table_alias.values() and table_alias.inv[geotable] != "":
                    geocol = f"{table_alias.inv[geotable]}.{geocol}"
                    pass 
                select.expressions.append(f"ST_Union({geocol}) AS geom")

    return parsed_query.sql()