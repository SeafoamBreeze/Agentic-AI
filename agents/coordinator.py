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

    system_prompt = """You are a player in an Among Us game who will be known as White.
    There are 4 players in this lobby, including yourself. 
    The other players will be known as Red, Blue and Green.
    There will be a total of 3 Crewmates and 1 imposter, randonly assigned.
    The identities of the players will remain unknown until the game ends.

    Players:
    - Red: Boy, lively and energetic, tries to make game fun for everyone
    - Blue: Boy, calm and collected, occassionally 
    - Green: Girl, valley girl speech pattern, dramatic

    Based on the conversation flow, select who should speak next to keep the conversation lively and natural.
    Consider:
    - Who hasn't spoken recently
    - Who has been accused of being the imposter
    - Most importantly, who would add interesting perspective
    - Natural kopitiam banter flow
 
    Respond with ONLY the speaker ID (Red, Blue, Green).
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
        valid_speakers = ["ah_seng", "mei_qi", "bala", "dr_tan"]
        if selected_speaker not in valid_speakers:
            # Fallback to round-robin if invalid
            import random
            selected_speaker = random.choice(valid_speakers)
            debug(f"Invalid speaker, fallback to: {selected_speaker}", "COORDINATOR")

    except Exception as e:
        # Fallback selection if LLM fails
        import random
        valid_speakers = ["ah_seng", "mei_qi", "bala", "dr_tan"]
        selected_speaker = random.choice(valid_speakers)
        debug(f"LLM error, random selection: {selected_speaker}", "COORDINATOR")

    debug(f"Final selection: {selected_speaker} (volley {volley_left} -> {volley_left - 1})", "COORDINATOR")

    # Return only the updates (LangGraph will merge with existing state)
    return {
        "next_speaker": selected_speaker,
        "volley_msg_left": volley_left - 1
    }
