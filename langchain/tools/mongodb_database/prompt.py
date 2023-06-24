# flake8: noqa
QUERY_CHECKER = """
{command}
Double check the MongoDB command above for common mistakes, including:
- Using $in or $nin with NULL values
- Using the proper operator for array elements
- Using the correct syntax for range queries
- Data type mismatch in predicates
- Properly specifying field paths
- Using the correct number of arguments for operators
- Casting to the correct data type when necessary
- Using the proper fields for joins in $lookup operations

If there are any of the above mistakes, rewrite the command. If there are no mistakes, just reproduce the original command."""
