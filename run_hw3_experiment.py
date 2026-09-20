from pathlib import Path
import csv
import json
import time
import numpy as np

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import (
    TokenTextSplitter,
    SemanticSplitterNodeParser,
    SentenceWindowNodeParser,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "reports" / "hw03" / "corpus"
RAW_DIR = ROOT / "reports" / "hw03" / "raw"
QUESTIONS_FILE = ROOT / "reports" / "hw03" / "questions.yaml"

RAW_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5


def load_questions():
    import yaml

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data["questions"]


def cosine_similarity(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)

    denom = np.linalg.norm(a) * np.linalg.norm(b)

    if denom == 0:
        return 0.0

    return float(np.dot(a, b) / denom)


def source_name(node):
    metadata = getattr(node, "metadata", {}) or {}

    for key in ("file_name", "filename", "source"):
        value = metadata.get(key)
        if value:
            return Path(str(value)).name

    return "UNKNOWN"


def make_chunkers(embed_model):
    return {
        "token": TokenTextSplitter(
            chunk_size=256,
            chunk_overlap=40,
        ),
        "semantic": SemanticSplitterNodeParser.from_defaults(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=embed_model,
        ),
        "sentence_window": SentenceWindowNodeParser.from_defaults(
            window_size=3,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        ),
    }


def retrieve_one(technique, index, embed_model, question, expected_source):
    query = question["question"]

    query_embedding = embed_model.get_text_embedding(query)

    retriever = index.as_retriever(
        similarity_top_k=TOP_K
    )

    start = time.perf_counter()
    retrieved = retriever.retrieve(query)
    latency_ms = (time.perf_counter() - start) * 1000

    rows = []

    for rank, item in enumerate(retrieved, start=1):
        node = item.node

        text = node.get_content()

        doc_embedding = embed_model.get_text_embedding(text)

        cosine_sim = cosine_similarity(
            query_embedding,
            doc_embedding,
        )

        store_score = getattr(item, "score", None)

        rows.append({
            "question_id": question["id"],
            "technique": technique,
            "rank": rank,
            "store_score": (
                float(store_score)
                if store_score is not None
                else None
            ),
            "cosine_sim": cosine_sim,
            "chunk_len": len(text),
            "source": source_name(node),
            "expected_source": expected_source,
            "source_match": source_name(node) == expected_source,
            "preview": " ".join(text.replace("\n", " ").split())[:160],
        })

    print()
    print("=" * 100)
    print(f"TECHNIQUE: {technique.upper()}")
    print(f"QUESTION: {question['id']} - {query}")
    print(f"Expected source: {expected_source}")
    print("=" * 100)

    print(
        f"Query embedding shape: "
        f"{np.asarray(query_embedding).shape}"
    )

    print(
        "First 8 query embedding values:",
        np.asarray(query_embedding[:8])
    )

    if rows:
        doc_vectors = np.vstack([
            embed_model.get_text_embedding(
                retrieved[i].node.get_content()
            )
            for i in range(len(rows))
        ])

        print(
            f"Document embedding matrix shape: "
            f"{doc_vectors.shape}"
        )

    print()
    print(
        f"{'Rank':<6}"
        f"{'Store Score':<16}"
        f"{'Cosine':<14}"
        f"{'Length':<10}"
        f"{'Source':<40}"
        f"Preview"
    )

    for row in rows:
        print(
            f"{row['rank']:<6}"
            f"{str(row['store_score']):<16}"
            f"{row['cosine_sim']:<14.4f}"
            f"{row['chunk_len']:<10}"
            f"{row['source']:<40}"
            f"{row['preview']}"
        )

    print(f"\nRetrieval latency: {latency_ms:.2f} ms")

    for row in rows:
        row["retrieval_latency_ms"] = latency_ms
        row["query_embedding_dimension"] = len(query_embedding)
        row["query_embedding_first_8"] = [
            float(x) for x in query_embedding[:8]
        ]

    return rows


def main():
    print("=" * 100)
    print("HW3 RETRIEVAL EXPERIMENT")
    print("=" * 100)
    print(f"Corpus: {CORPUS_DIR}")
    print(f"Model: {MODEL_NAME}")
    print(f"Top-k: {TOP_K}")

    if not CORPUS_DIR.exists():
        raise FileNotFoundError(
            f"Corpus directory does not exist: {CORPUS_DIR}"
        )

    questions = load_questions()

    print("\nLoading corpus...")

    documents = SimpleDirectoryReader(
        input_dir=str(CORPUS_DIR),
        recursive=True,
    ).load_data()

    print(f"Loaded documents: {len(documents)}")

    if not documents:
        raise RuntimeError("No corpus documents were loaded.")

    print("\nLoading embedding model...")

    embed_model = HuggingFaceEmbedding(
        model_name=MODEL_NAME
    )

    chunkers = make_chunkers(embed_model)

    all_results = []
    metrics = []

    for technique, chunker in chunkers.items():

        print("\n" + "#" * 100)
        print(f"BUILDING: {technique.upper()}")
        print("#" * 100)

        print("Chunking documents...")

        nodes = chunker.get_nodes_from_documents(documents)

        print(f"Number of chunks: {len(nodes)}")

        if not nodes:
            raise RuntimeError(
                f"No nodes generated for {technique}"
            )

        lengths = [
            len(node.get_content())
            for node in nodes
        ]

        print(
            f"Average chunk length: "
            f"{np.mean(lengths):.2f}"
        )

        print("Building in-memory VectorStoreIndex...")

        index = VectorStoreIndex(
            nodes,
            embed_model=embed_model,
        )

        technique_results = []

        for question in questions:

            results = retrieve_one(
                technique=technique,
                index=index,
                embed_model=embed_model,
                question=question,
                expected_source=question["expected_source"],
            )

            technique_results.extend(results)
            all_results.extend(results)

        jsonl_path = RAW_DIR / f"{technique}_results.jsonl"

        with open(jsonl_path, "w", encoding="utf-8") as f:
            for row in technique_results:
                f.write(
                    json.dumps(row, ensure_ascii=False)
                    + "\n"
                )

        csv_path = RAW_DIR / f"{technique}_results.csv"

        if technique_results:
            fieldnames = list(technique_results[0].keys())

            with open(
                csv_path,
                "w",
                newline="",
                encoding="utf-8",
            ) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                )
                writer.writeheader()
                writer.writerows(technique_results)

        top1 = [
            r["cosine_sim"]
            for r in technique_results
            if r["rank"] == 1
        ]

        all_cosines = [
            r["cosine_sim"]
            for r in technique_results
        ]

        recalls = []

        for question in questions:
            qrows = [
                r
                for r in technique_results
                if r["question_id"] == question["id"]
            ]

            recalls.append(
                any(r["source_match"] for r in qrows)
            )

        latencies = [
            r["retrieval_latency_ms"]
            for r in technique_results
        ]

        metrics.append({
            "technique": technique,
            "num_chunks": len(nodes),
            "avg_chunk_length": float(np.mean(lengths)),
            "top1_cosine_mean": (
                float(np.mean(top1))
                if top1 else 0.0
            ),
            "mean_at_k_cosine": (
                float(np.mean(all_cosines))
                if all_cosines else 0.0
            ),
            "recall_at_k": (
                float(np.mean(recalls))
                if recalls else 0.0
            ),
            "mean_retrieval_latency_ms": (
                float(np.mean(latencies))
                if latencies else 0.0
            ),
        })

    combined_jsonl = RAW_DIR / "all_results.jsonl"

    with open(
        combined_jsonl,
        "w",
        encoding="utf-8",
    ) as f:
        for row in all_results:
            f.write(
                json.dumps(row, ensure_ascii=False)
                + "\n"
            )

    metrics_path = ROOT / "reports" / "hw03" / "METRICS.md"

    with open(
        metrics_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write("# HW3 Retrieval Metrics\n\n")

        f.write(
            "| Technique | # Chunks | Avg Chunk Length | "
            "Top-1 Cosine | Mean@k Cosine | Recall@k | "
            "Mean Retrieval Latency (ms) |\n"
        )

        f.write(
            "|---|---:|---:|---:|---:|---:|---:|\n"
        )

        for m in metrics:
            f.write(
                f"| {m['technique']} "
                f"| {m['num_chunks']} "
                f"| {m['avg_chunk_length']:.2f} "
                f"| {m['top1_cosine_mean']:.4f} "
                f"| {m['mean_at_k_cosine']:.4f} "
                f"| {m['recall_at_k']:.4f} "
                f"| {m['mean_retrieval_latency_ms']:.2f} |\n"
            )

    print("\n" + "=" * 100)
    print("FINAL METRICS")
    print("=" * 100)

    for m in metrics:
        print(
            f"{m['technique']:<18}"
            f"chunks={m['num_chunks']:<7}"
            f"avg_len={m['avg_chunk_length']:<10.2f}"
            f"top1={m['top1_cosine_mean']:<10.4f}"
            f"mean@k={m['mean_at_k_cosine']:<10.4f}"
            f"recall@k={m['recall_at_k']:<8.4f}"
            f"latency={m['mean_retrieval_latency_ms']:.2f}ms"
        )

    print("\nFiles written:")
    print(f"  {RAW_DIR}")
    print(f"  {metrics_path}")
    print(f"  {combined_jsonl}")

    print("\nHW3 EXPERIMENT COMPLETE.")


if __name__ == "__main__":
    main()
