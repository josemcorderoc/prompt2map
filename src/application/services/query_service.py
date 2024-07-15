import numpy as np
from sqlglot import parse_one, exp

from application.interfaces.text_similarity import TextSimilarity


class QueryService:
    def __init__(self, similarity: TextSimilarity):
        self.similarity = similarity
    
    def replace_literals(self, query: str, literals: dict[str, list[(str, np.ndarray)]]):
        parsed_query = parse_one(query)
        table_alias = {t.alias:t.name for t in parsed_query.find_all(exp.Table)}
        eqs = [eq for eq in parsed_query.find(exp.Where).find_all(exp.EQ)]
        for eq in eqs:
            literal = eq.find(exp.Literal)
            column = eq.find(exp.Column)
            if literal is None or column is None:
                continue
            table_name = column.table if column.table in literals else literals[column.table]
            
            most_similar_literal = self.similarity.most_similar(query, [query])
            literal.replace()
            
            