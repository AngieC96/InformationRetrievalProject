# Information Retrieval Project
Repository for the project of the course "Information Retrieval" of the master degree "Data Science and Scientific Computing" @UniTS

Implementation in Python of an Information Retrieval system using the Boolean Model.

The IR system is able to:

- answer boolean queries with AND, OR, and NOT. The system is also able to evaluate complex queries, even with many nested parentheses, like

  `"hello OR ((how AND (are OR you) OR I AND (am AND fine) OR I) AND am AND (sleepy OR hungry) AND cold)"`.

  - Use the `and_query` function to conect all the words in your query text with ANDs.
  - Use the `or_query` function to connect all the words in your query text with ORs.
  - Use the `not_query` function to connect all the words in your query text with NOTs.
  - Use the `query` function to answer a query with AND, OR and NOT without parentheses.
  - Use the `query_with_pars` function to answer complex queries with AND, OR or NOT with parentheses, also nested.

- answer phrase queries using a positional index and also answer to queries like “$\texttt{term}_1 /k \texttt{ term}_2$”, with $k$ an integer indicating the maximum number of words that can be between $\texttt{term}_1$ and $\texttt{term}_2$

- answer wildcards queries using a permuterm index

- perform normalization

- perform on demand spelling correction, using the edit distance

  (for time reasons keeping as correct the first character and searching only among the terms in the index that start with that character, but changing a parameter allows for a search in the entire index)

I evaluated the IR system on a set of test queries for each functionality, checking the results using `assert`s.

I also implemented a way to save and load the entire index from disk, to avoid re-indexing when the program starts. To save the index I used `Pickle`.



## Dataset

Dataset that I use: http://www.cs.cmu.edu/~ark/personas/, with more than 42k movie descriptions.