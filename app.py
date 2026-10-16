"""Streamlit interface for the local Finance AI Analyst."""
import streamlit as st
from ai.finance_ai import ask_finance_ai

st.set_page_config(page_title="Finance AI Analyst", page_icon="💰", layout="wide")
st.title("💰 Finance AI Analyst")
st.caption("Ask finance questions in natural language and query approved PostgreSQL reporting views using local Ollama.")
st.divider()

example_questions = [
    "What was our total revenue in 2025?",
    "Show me the top 5 overdue customers.",
    "Show me the top 5 outstanding vendors.",
    "What was our net profit in 2025?",
    "What is our DSO?",
    "What is our DPO?",
]
selected_example = st.selectbox("Try an example question", ["Choose an example..."] + example_questions)
question = st.text_input(
    "Ask your finance question",
    value="" if selected_example == "Choose an example..." else selected_example,
    placeholder="e.g. What was our total revenue in 2025?",
    max_chars=500,
)

if st.button("🚀 Ask Finance AI", type="primary", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a finance question first.")
    else:
        with st.spinner("Checking the question, generating SQL and querying PostgreSQL..."):
            try:
                result = ask_finance_ai(question.strip())
                st.success(f"Query completed. {len(result['data']):,} row(s) returned.")
                st.subheader("📊 Result")
                st.dataframe(result["data"], use_container_width=True, hide_index=True)
                with st.expander("🔍 View validated SQL"):
                    st.code(result["sql"], language="sql")
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("The query could not be completed. Check the local database connection and application logs.")

st.divider()
st.caption("Local prototype • PostgreSQL • Ollama • Qwen 2.5 3B")
