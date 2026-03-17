---
name: simple_rag_pipeline
tags: [rag, retrieval, embeddings, generation, search, documents]
trigger: task involves building a retrieval-augmented generation pipeline or searching documents with embeddings
type: pattern
version: 1
success_count: 0
fail_count: 0
---
# Simple RAG Pipeline
## Purpose
Implement a basic Retrieval-Augmentation-Generation pipeline for generating responses to queries based on a set of text documents.

## When to use
Use this skill when you need to build a simple information retrieval and generation system that leverages embeddings for document ranking and an LLM for response generation.

## How to use
1. **Install Required Libraries**: `pip install sentence-transformers numpy scipy torch`
2. **Prepare Documents and Query**: Have your text documents and query ready.
3. **Embed Documents and Query**: Use `sentence-transformers` to create embeddings.
4. **Calculate Cosine Similarity**: Rank documents by similarity to the query.
5. **Pass Context to LLM**: Use the top-N retrieved documents as context for generation.

## Example use case
Automate customer support by generating responses to user queries based on a knowledge base of documents.
