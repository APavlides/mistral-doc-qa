## Step 1


Document Q&A (embeddings, a simple RAG)
  - Basic version: paste or upload some text, ask a question, and get an answer from that text.....My thoughts: it is probably best not to use a vector db. Instead we store a document in memory, we chunk it, we store this as a json file. Because of --reload, we need the json file otherwise the memory will be lost on each reload. We will use the mistral embedding endpoint. And we will use cosine similarity to match embeddings in a python list

## Step 2

if i wanted to change from a doc.json to using a database what would be the best solution. can i USE Mysql (part of standard python library), do I need postgres (which can store embeddings), or is there another better choice for a poc

## Step 3

I want to move from a doc.json file for storage to a sqlite (built in python standard library).
