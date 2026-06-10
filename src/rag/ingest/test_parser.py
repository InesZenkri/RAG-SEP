from rag.ingest.parser import parse_document

doc = parse_document("src/rag/ingest/sample1.pdf")

print("doc_id:", doc.doc_id)
print("source:", doc.source)
print("title:", doc.title)
print("num_pages:", doc.num_pages)
print("first page preview:", doc.pages[0][:500])
