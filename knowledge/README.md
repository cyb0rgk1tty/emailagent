# Knowledge Base - Supplement Products & Services

This directory contains the knowledge base documents used by the RAG system to generate accurate, contextual email responses.

## Structure

- `products/` - Product catalogs (probiotics, electrolytes, protein, greens, etc.)
- `pricing/` - Pricing guides and MOQ requirements
- `capabilities/` - Manufacturing capabilities and services
- `certifications/` - Available certifications (Organic, GMP, NSF, etc.)
- `faq/` - Frequently asked questions

## Supported Formats

- Markdown (.md)
- PDF (.pdf)
- Microsoft Word (.docx)
- Plain text (.txt)

## Adding Documents

1. Place documents in the appropriate subdirectory
2. Run the ingestion script:
```bash
python scripts/ingest_knowledge.py
```

3. Documents will be chunked, embedded, and stored in PostgreSQL with pgvector

## Re-indexing

To re-index all documents after updates:
```bash
python scripts/update_knowledge.py
```

## Document Guidelines

- Use clear, professional language
- Include specific details (MOQs, pricing, certifications)
- Keep information up-to-date
- Use consistent formatting
- Add source attribution when applicable
