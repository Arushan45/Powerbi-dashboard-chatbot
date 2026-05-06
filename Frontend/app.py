import requests
import streamlit as st

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="AI Production Assistant",
    page_icon="🤖",
    layout="wide",
)

# -----------------------------
# Constants
# -----------------------------
DEFAULT_PLANT = "UNIDIL"
BACKEND_CHAT_URL = "http://localhost:8000/api/chat"


# -----------------------------
# Helpers
# -----------------------------
def get_plant_from_url(default_plant: str = DEFAULT_PLANT) -> str:
    """
    Read the `plant` query parameter from the URL.
    Falls back to default_plant when missing/empty.
    """
    plant_param = st.query_params.get("plant", default_plant)

    # st.query_params.get may return a list in some Streamlit versions/flows.
    if isinstance(plant_param, list):
        plant_param = plant_param[0] if plant_param else default_plant

    plant_value = str(plant_param).strip()
    return plant_value if plant_value else default_plant


def initialize_session_state() -> None:
    """Initialize required session state keys once."""
    if "plant_context" not in st.session_state:
        st.session_state.plant_context = get_plant_from_url()

    if "messages" not in st.session_state:
        st.session_state.messages = []


# -----------------------------
# App start
# -----------------------------
initialize_session_state()
active_plant = st.session_state.plant_context

# Enterprise-friendly, clean header
st.title(f"AI Production Assistant - {active_plant}")
st.caption("Context-aware assistant embedded for manufacturing dashboard workflows.")

# Render existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture user input
user_message = st.chat_input("Ask about production performance, anomalies, or KPIs...")

if user_message:
    # Show and store user message
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    payload = {
        "user_message": user_message,
        "plant_context": active_plant,
    }

    # Send message + context to backend and handle failures gracefully
    try:
        response = requests.post(BACKEND_CHAT_URL, json=payload, timeout=30)
        response.raise_for_status()

        response_data = response.json()

        # Flexible key handling so minor backend schema changes do not break UI.
        assistant_message = (
            response_data.get("assistant_message")
            or response_data.get("response")
            or response_data.get("message")
            or "I received your request but no response text was returned by the backend."
        )

        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_message}
        )

        with st.chat_message("assistant"):
            st.markdown(assistant_message)

    except requests.exceptions.RequestException as exc:
        error_text = f"Backend connection failed: {exc}"
        st.error(error_text)

        fallback_message = (
            "I cannot reach the AI service right now. Please try again shortly."
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": fallback_message}
        )

        with st.chat_message("assistant"):
            st.markdown(fallback_message)
