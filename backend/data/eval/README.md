# Evaluation Dataset Format

Each entry includes document text and expected issues for benchmarking.

Schema:
```
{
  "document_id": "string",
  "pages": { "1": "text", "2": "text" },
  "expected_issues": [
    {
      "category": "name|date|financial|other",
      "field": "string",
      "expected": "string|null",
      "found": "string|null"
    }
  ]
}
```
