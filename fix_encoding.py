import pathlib
for name in ["health_relevance.py", "swarm_search_generic_books.py"]:
    p = pathlib.Path(name)
    if p.exists():
        data = p.read_bytes().replace(b"\x00", b"")
        p.write_bytes(data)
        print(f"fixed {name} len={len(data)}")
