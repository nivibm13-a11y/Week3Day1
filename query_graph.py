import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_openai import ChatOpenAI


def get_neo4j_password():
    load_dotenv()
    for key, value in os.environ.items():
        if key.upper().endswith("PASSWORD") and value:
            return value
    return None


load_dotenv()


print("Connecting to Neo4j database...")
password = get_neo4j_password()
missing = [
    ("NEO4J_URI", os.getenv("NEO4J_URI")),
    ("NEO4J_USERNAME", os.getenv("NEO4J_USERNAME")),
    ("DB_PASSWORD", password),
]
missing_names = [name for name, value in missing if not value]
if missing_names:
    raise ValueError("Missing environment variables: " + ", ".join(missing_names))

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=password,
)

graph.refresh_schema()

CYPHER_GENERATION_TEMPLATE = """Task: Generate a Cypher query to answer the user's question.
The database contains nodes with label `Scheme`.
LangChain's graph transformer typically stores the scheme text/description in the `id` property or `name` property.
When searching for keywords like "farmers", "women", or specific topics, check if `toLower(s.id) CONTAINS toLower('keyword')` or `toLower(s.name) CONTAINS toLower('keyword')`.

Schema:
{schema}

Question:
{question}

Cypher Query:"""

CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

cypher_chain = GraphCypherQAChain.from_llm(
    llm=ChatOpenAI(temperature=0, model="gpt-4o-mini"),
    graph=graph,
    cypher_prompt=CYPHER_PROMPT,
    verbose=True,
    allow_dangerous_requests=True,
)

print("\nKnowledge Graph Ready! Ask anything about the schemes.\n")

while True:
    question = input("Your Question: ").strip()
    if question.lower() in ["exit", "quit"]:
        break
    if not question:
        continue

    try:
        response = cypher_chain.invoke(question)
        print("\n--- Answer ---")
        print(response["result"])
        print("-" * 40 + "\n")
    except Exception as e:
        print(f"An error occurred: {e}\n")
