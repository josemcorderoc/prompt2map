from bidict import bidict
import numpy as np
from sqlglot import parse_one, exp


def is_read_only_query(query: str) -> bool:
    parsed_query = parse_one(query)
    if parsed_query is None:
            raise ValueError(f"Query {query} could not be parsed.")
    expression = parsed_query.find(exp.Insert, exp.Update, exp.Delete)
    return expression is None


def to_geospatial_query(query: str, geom_table: str, geom_col: str, agg_function: str, ) -> str:
    parsed_query = parse_one(query)
    table_alias = bidict({t.alias:t.name for t in parsed_query.find_all(exp.Table)})
    table_names = [t.name for t in parsed_query.find_all(exp.Table)]
    
    if parsed_query is None:
        raise ValueError(f"Query {query} could not be parsed.")
    
    if geom_table not in table_names:
        raise ValueError(f"Geotable {geom_table} not found in query.")
    
    select = parsed_query.find(exp.Select)
    group_by = parsed_query.find(exp.Group)
    
    if select is None:
        raise ValueError(f"Query {query} does not contain a SELECT clause.")
    
    if group_by is None:
        new_column = exp.Column(this=exp.Identifier(this=geom_col))
        select.expressions.append(new_column)   
    else:
        group_by_tables = [table_alias[e.table] for e in group_by.expressions 
                           if type(e) == exp.Column 
                            and e.table in table_alias 
                            and table_alias[e.table] != geom_table]
        if geom_table not in group_by_tables:
            geom_col_name = geom_col
            if geom_table in table_alias.values() and table_alias.inv[geom_table] != "":
                geom_col_name = f"{table_alias.inv[geom_table]}.{geom_col}"
            select.expressions.append(f"{agg_function}({geom_col_name}) AS {geom_col}")

    return parsed_query.sql()