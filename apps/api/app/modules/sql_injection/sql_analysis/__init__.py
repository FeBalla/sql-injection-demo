"""Understanding the SQL text of the statement preview.

A small, dialect-aware lexer answers three questions about a statement:

* how to color each character (``keyword``, ``string``, ``param``, ``plain``, or ``input`` /
  ``escaped`` for characters that came from user input),
* how many statements the database will see (top-level ``;`` outside strings and comments),
* which input values escape the string literal the template put them in.

It is not a full parser: it only knows enough of each dialect's literal, identifier and comment
syntax to find where strings start and end, which is exactly what SQL injection abuses.

Modules, in reading order:

* ``dialects``: the per-database syntax rules (quotes, comments, parameters) and keywords,
* ``lexer``: splits SQL into tokens and scans quoted literals,
* ``escapes``: finds the part of an input value that ends up outside its string literal,
* ``analysis``: :func:`analysis.analyze`, the entry point that combines the above.
"""
