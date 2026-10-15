import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_openai import ChatOpenAI
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="TN Government Scheme Navigator",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern Custom Styling (CSS for clean forms)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        font-size: 1.05rem;
        opacity: 0.9;
    }
    .result-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #2e7d32;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-top: 1.5rem;
    }
    .stButton button {
        background-color: #ffffff;
        color: #2e7d32;
        border: 1px solid #c8e6c9;
        border-radius: 8px;
        font-weight: 500;
        text-align: left;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #e8f5e9;
        border-color: #2e7d32;
        color: #1b5e20;
    }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_graph_resources():
  load_dotenv()
  graph = Neo4jGraph(
      url=os.getenv("NEO4J_URI"),
      username=os.getenv("NEO4J_USERNAME"),
      password=os.getenv("NEO4J_PASSWORD"),
  )
  graph.refresh_schema()

  cypher_chain = GraphCypherQAChain.from_llm(
      llm=ChatOpenAI(temperature=0, model="gpt-4o-mini"),
      graph=graph,
      verbose=True,
      allow_dangerous_requests=True,
  )
  return graph, cypher_chain


try:
  graph_db, cypher_chain = init_graph_resources()
except Exception as e:
  st.error(f"Failed to connect to Neo4j database: {e}")
  st.stop()


# Universal Keyword Search Fallback
def search_graph_manually(keyword):
  query = """
    MATCH (s:Scheme)
    WHERE any(prop in keys(s) WHERE toLower(toString(s[prop])) CONTAINS toLower($kw))
    RETURN properties(s) AS props
    LIMIT 10
    """
  results = graph_db.query(query, params={"kw": keyword})
  if not results:
    return None

  response_text = f"### 🌾 Schemes found for **'{keyword.capitalize()}'**\n\n"
  for idx, record in enumerate(results, 1):
    props = record["props"]
    text_content = props.get("id") or props.get("name") or str(props)
    response_text += f"**{idx}.** {text_content}\n\n---\n\n"
  return response_text


# --- Initialize Session State for Single-Turn Query ---
if "current_question" not in st.session_state:
  st.session_state.current_question = ""
if "current_answer" not in st.session_state:
  st.session_state.current_answer = None

# --- SIDEBAR ---
with st.sidebar:
  st.image("https://img.icons8.com/color/96/government.png", width=60)
  st.title("TN Navigator")
  st.markdown("Explore government welfare programs using AI & Knowledge Graphs.")
  st.markdown("---")

  st.subheader("💡 Quick Prompt Suggestions")
  example_questions = [
      "List all the schemes related to farmers.",
      "What are the details of the Pudhumai Penn Scheme?",
      "Which schemes provide subsidies for seed production?",
      "List all schemes for women.",
  ]

  for eq in example_questions:
    if st.button(eq, use_container_width=True):
      st.session_state.current_question = eq
      st.rerun()

  st.markdown("---")
  st.caption("Engineered with Neo4j, LangChain & Streamlit")

# --- MAIN CONTENT AREA ---
st.markdown(
    """
    <div class="main-header">
        <h1>Tamil Nadu Government Scheme Assistant</h1>
        <p>Type a question or select a suggestion below to search welfare programs instantly.</p>
    </div>
""",
    unsafe_allow_html=True,
)

# Form input so hitting Enter or clicking search clears/replaces the view
with st.form(key="query_form"):
  user_input = st.text_input(
      "🔍 Ask a question about government schemes:",
      value=st.session_state.current_question,
      placeholder="e.g., What schemes are available for farmers?",
  )
  submit_button = st.form_submit_button(
      label="Get Answer", use_container_width=True
  )

if submit_button and user_input:
  st.session_state.current_question = user_input
  with st.spinner("Analyzing Knowledge Graph relationships..."):
    try:
      lower_prompt = user_input.lower()
      if "farmer" in lower_prompt or "agriculture" in lower_prompt:
        answer = search_graph_manually("farmer")
      elif "women" in lower_prompt or "female" in lower_prompt:
        answer = search_graph_manually("women")
      elif "seed" in lower_prompt:
        answer = search_graph_manually("seed")
      else:
        response = cypher_chain.invoke(user_input)
        answer = response.get("result", "I couldn't find an answer.")

      if not answer:
        answer = "I couldn't find any matching schemes for that query."

      st.session_state.current_answer = answer
    except Exception as err:
      st.session_state.current_answer = (
          f"An error occurred while querying the graph: {err}"
      )
  st.rerun()

# Display the current result card if an answer exists
if st.session_state.current_answer:
  st.markdown(
      f"""
    <div class="result-card">
        <h3>Result for: <i>"{st.session_state.current_question}"</i></h3>
        <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
    </div>
    """,
      unsafe_allow_html=True,
  )
  st.markdown(st.session_state.current_answer)

  # Clear button to reset the view for a new question
  if st.button("🔄 Ask Another Question"):
    st.session_state.current_question = ""
    st.session_state.current_answer = None
    st.rerun()