import logging
from sqlglot import parse_one, exp
import sqlparse

from prompt2map.interfaces.nlp.embedding import Embedding
from prompt2map.interfaces.sql.geo_database import GeoDatabase

# Function to remove a specific condition from the WHERE clause
def remove_condition(parsed_query, column, value):
    # Ensure the query has a WHERE clause
    if not parsed_query.args.get("where"):
        return parsed_query

    # Traverse the WHERE clause to find the condition to remove
    where_clause = parsed_query.args["where"]
    conditions = where_clause.expressions if isinstance(where_clause, exp.And) else [where_clause]

    new_conditions = [
        condition for condition in conditions
        if not (isinstance(condition, exp.EQ) and
                condition.left.text('') == column and
                condition.right.text('') == value)
    ]

    # Update the WHERE clause with the new conditions
    if new_conditions:
        parsed_query.set("where", exp.And(this=new_conditions[0], expressions=new_conditions[1:]))
    else:
        del parsed_query.args["where"]

    return parsed_query

def prettify_sql(query: str) -> str:
    return sqlparse.format(query, reindent=True, keyword_case='upper')
    
class SQLQueryProcessor:
    def __init__(self, db: GeoDatabase, embedding: Embedding
                 ) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
        self.embedding = embedding
    
    def get_sql_literals(self, parsed_query: exp.Expression) -> dict[tuple[str, str], exp.Literal]:
        # parsed_query = parse_one(query)
        table_alias = {t.alias:t.name for t in parsed_query.find_all(exp.Table)}
        
        table_names = [t.name for t in parsed_query.find_all(exp.Table)]
        if len(table_names) == 0:
            raise ValueError(f"Query {parsed_query.sql()} does not contain any table names.")
        
        where = parsed_query.find(exp.Where)
        if where is None:
            return {}
        
        literals: dict[tuple[str, str], exp.Literal] = {}
        for eq in where.find_all(exp.EQ):
            literal, column  = eq.find(exp.Literal), eq.find(exp.Column)
            if literal is None or column is None:
                continue
            
            table_name = column.table
            column_name = column.name
            
            if table_name in table_alias:
                    table_name = table_alias[table_name]
            elif table_name == "":
                    table_name = table_names[0]
                    
            literals[(table_name, column_name)] = literal
                    
        return literals

    def replace_literals(self, query: str) -> str:
        """Replace literals in a query with the most similar literal from a list of literals. Only string literals are replaced.

        Args:
            query (str): SQL query
            literals (dict[tuple[str, str], list[str]]): key: (table, column), value: list of all possible literals
            similarity (TextSimilarity): object to calculate similarity between strings

        Raises:
            ValueError: Query could not be parsed
            ValueError: Query does not contain any table names

        Returns:
            str: SQL query with literals replaced
        """
        parsed_query = parse_one(query)
        query_literals = self.get_sql_literals(parsed_query)
        if len(query_literals) == 0:
            self.logger.warning(f"Query {query} does not contain any literals.")
            return query
        
        self.logger.info(f"Query literals: {query_literals}")
        for (table_name, column_name), literal in query_literals.items():
            col_type = self.db.get_column_type(table_name, column_name)
            if col_type is None:
                self.logger.warning(f"Column {column_name} in table {table_name} does not exist.")
                continue
            elif col_type.lower() not in ["text", "varchar"]:
                self.logger.warning(f"Literal {literal} in column {column_name} in table {table_name} is not a string.")
                continue
            
            literal_contained = self.db.value_in_column(table_name, column_name, str(literal))
            if literal_contained:
                self.logger.info(f"Literal {literal} is already in column {column_name} in table {table_name}.")
                continue
            
            # Replace the literal with the most similar literal
            text_embedding = self.embedding.get_embedding(str(literal)).tolist()
            most_similar_literal = self.db.get_most_similar_cosine(table_name, column_name, text_embedding, "emb_openai_small")
            most_similar_literal = f"'{most_similar_literal}'"
            self.logger.info(f"Replacing literal {literal} with {most_similar_literal} (most similar).")
            literal.replace(most_similar_literal)
                
            
        return parsed_query.sql()

    