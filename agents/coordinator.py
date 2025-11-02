from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from utils import debug


def coordinator(state):
    """
    Select next speaker based on conversation context.
    Manages volley control and updates state accordingly.

    Updates state with:
    - next_speaker: Selected agent ID or "human"
    - volley_msg_left: Decremented counter

    Returns: Updated state
    """

    debug(state)
    volley_left = state.get("volley_msg_left", 0)
    debug(f"Volley messages left: {volley_left}", "COORDINATOR")

    if volley_left <= 0:
        debug("No volleys left, returning to human", "COORDINATOR")
        return {
            "next_speaker": "human",
            "volley_msg_left": 0
        }

    messages = state.get("messages", [])

    conversation_text = ""
    for msg in messages:
        # Messages are now always dicts
        conversation_text += f"{msg.get('content', '')}\n"

    system_prompt = """
    You are managing a lively conversation at a Singapore kopitiam.

    Available speakers:
    - mei_qi: Young 21yo content creator, social media savvy, knows latest news and trends, also curious about bird sightings
    - bala: Ex-statistician turned football tipster, dry humor, analytical, enjoys spotting patterns 
    - dr_tan: Retired 72yo philosophy professor, thoughtful and deep thinker, likes sharing interesting facts 

    Based on the conversation flow, select who should speak next to keep the conversation lively and natural.
    Consider:
    - Who hasn't spoken recently
    - Who has relevant expertise or interest for the current topic
    - Who would add an interesting perspective
    - Natural kopitiam banter flow
    - mei_qi should speak more about social media, trends, and recent bird sightings or news she just saw
    - bala may analyze bird sightings data or provide witty observations
    - dr_tan may add philosophical or fun factual insights about birds

    Respond with ONLY the speaker ID (mei_qi, bala, or dr_tan).
    """

    user_prompt = f"""Recent conversation:
{conversation_text}

Who should speak next to help deduce the imposter?"""

    debug("Analyzing conversation context...", "COORDINATOR")

    # Call LLM
    try:
        llm = ChatOpenAI(model="gpt-5-nano", temperature=1)

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # Extract speaker from response
        if isinstance(response.content, list):
            selected_speaker = " ".join(str(item) for item in response.content).strip().lower()
        else:
            selected_speaker = str(response.content).strip().lower()
        debug(f"LLM selected: {selected_speaker}", "COORDINATOR")

        # Validate speaker
        valid_speakers = ["mei_qi", "bala", "dr_tan"]
        if selected_speaker not in valid_speakers:
            # Fallback to round-robin if invalid
            import random
            selected_speaker = random.choice(valid_speakers)
            debug(f"Invalid speaker, fallback to: {selected_speaker}", "COORDINATOR")

    except Exception as e:
        # Fallback selection if LLM fails
        import random
        valid_speakers = ["mei_qi", "bala", "dr_tan"]
        selected_speaker = random.choice(valid_speakers)
        debug(f"LLM error, random selection: {selected_speaker}", "COORDINATOR")

    debug(f"Final selection: {selected_speaker} (volley {volley_left} -> {volley_left - 1})", "COORDINATOR")

    # Return only the updates (LangGraph will merge with existing state)
    return {
        "next_speaker": selected_speaker,
        "volley_msg_left": volley_left - 1
    }
