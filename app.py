"""Streamlit interface for the Finance AI Analyst."""
import pandas as pd
import streamlit as st

from ai.finance_ai import ask_finance_ai

st.set_page_config(page_title="Finance AI Analyst", page_icon="💰", layout="wide")
st.title("💰 Finance AI Analyst")
st.caption("Ask finance questions in natural language and query approved PostgreSQL reporting views.")
st.divider()


def format_inr(value):
    """Format numeric finance values in Indian currency units."""
    number = float(value)
    sign = "-" if number < 0 else ""
    number = abs(number)
    if number >= 10_000_000:
        return f"{sign}₹{number / 10_000_000:,.2f} crore"
    if number >= 100_000:
        return f"{sign}₹{number / 100_000:,.2f} lakh"
    return f"{sign}₹{number:,.2f}"


def is_money_column(column_name):
    """Identify likely monetary columns without formatting counts or percentages."""
    name = str(column_name).lower()
    money_terms = (
        "revenue", "profit", "cash", "amount", "balance", "expense", "sales",
        "receivable", "payable", "outstanding", "budget", "payment", "cost",
        "invoice", "collection", "purchase", "recovery", "income",
    )
    return any(term in name for term in money_terms)


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
        with st.spinner("Generating validated SQL and querying PostgreSQL..."):
            try:
                result = ask_finance_ai(question.strip())
                data = result["data"]
                st.success(f"Query completed. {len(data):,} row(s) returned.")
                st.subheader("📊 Answer")

                # For a single-value monetary answer, show a clear KPI rather than scientific notation.
                if len(data) == 1 and len(data.columns) == 1:
                    col = data.columns[0]
                    value = data.iloc[0, 0]
                    if pd.api.types.is_numeric_dtype(data[col]) and is_money_column(col) and pd.notna(value):
                        st.metric(label=str(col).replace("_", " ").title(), value=format_inr(value))
                    else:
                        st.write(value)

                st.subheader("📋 Result Details")
                display_data = data.copy()
                for col in display_data.columns:
                    if is_money_column(col) and pd.api.types.is_numeric_dtype(display_data[col]):
                        display_data[col] = display_data[col].map(
                            lambda value: format_inr(value) if pd.notna(value) else "—"
                        )
                st.dataframe(display_data, use_container_width=True, hide_index=True)
                with st.expander("🔍 View validated SQL"):
                    st.code(result["sql"], language="sql")
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"The query could not be completed: {exc}")

st.divider()
st.caption("Local prototype • PostgreSQL • Groq or Ollama, depending on your .env settings")
