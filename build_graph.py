import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from scraper import extract_schemes


def get_neo4j_password():
    load_dotenv()
    for key, value in os.environ.items():
        if key.upper().endswith("PASSWORD") and value:
            return value
    return None


load_dotenv()


def main():
    password = get_neo4j_password()
    missing = [
        ("NEO4J_URI", os.getenv("NEO4J_URI")),
        ("NEO4J_USERNAME", os.getenv("NEO4J_USERNAME")),
        ("DB_PASSWORD", password),
    ]
    missing_names = [name for name, value in missing if not value]
    if missing_names:
        raise ValueError("Missing environment variables: " + ", ".join(missing_names))

    print("Connecting to Neo4j...")
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=password,
    )

    raw_schemes = extract_schemes()
    if not raw_schemes:
        print("No data found to process.")
        return

    documents = [
        Document(
            page_content=(
                f"Scheme Name: {s['scheme_name']}. Description: {s['details']}"
            )
        )
        for s in raw_schemes
    ]

    print("Initializing LLM Graph Transformer with enhanced schema...")
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")

    llm_transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=[
            "Scheme",
            "Department",
            "Beneficiary",
            "Benefit",
            "Eligibility",
            "Objective",
        ],
        allowed_relationships=[
            "BELONGS_TO",
            "TARGETS",
            "PROVIDES",
            "REQUIRES",
            "HAS_OBJECTIVE",
        ],
    )

    print("Extracting graph elements from all schemes using LLM...")
    graph_documents = llm_transformer.convert_to_graph_documents(documents)

    print("Writing complete graph documents to Neo4j...")
    graph.add_graph_documents(graph_documents)
    print(
        "Full Knowledge Graph successfully built and populated with all"
        " schemes!"
    )


if __name__ == "__main__":
    main()
