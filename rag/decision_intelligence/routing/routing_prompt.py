"""
routing_prompt.py

Purpose
-------
Builds the routing prompt used by the
Intent Router.

The routing prompt is responsible for
classifying the user's request into one
of the predefined system intents.

This prompt DOES NOT answer the user.

It ONLY performs intent classification.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import List, Dict


def build_routing_prompt(
    conversation_history: List[Dict],
    current_query: str,
):
    """
    Build the routing prompt.

    Parameters
    ----------
    conversation_history
        Previous conversation.

    current_query
        Current user query.

    Returns
    -------
    str
        Prompt sent to Grok.
    """

    history = ""

    if conversation_history:

        for message in conversation_history:

            role = message["role"].upper()

            content = message["message"]

            history += f"{role}: {content}\n"

    prompt = f"""
You are an Intent Classification Engine.

You are NOT an assistant.

You are NOT allowed to answer questions.

Your ONLY responsibility is to classify
the user's intent.

--------------------------------------------------

Project

This system is an Intelligent Credit Decision
Support Platform.

It contains four capabilities.

GENERAL
General conversation.

KNOWLEDGE
Questions regarding bank policy,
loan policy,
credit policy,
risk,
regulations,
or documentation.

DECISION
Questions asking why a prediction
was generated,
why a loan was rejected,
why SHAP values changed,
or asking for explanation of a prediction.

SIMULATION
Questions asking to modify applicant
information.

Examples include

What if income becomes 80000?

Suppose DTI decreases.

If grade changes from B5 to A2.

--------------------------------------------------

Classification Rules

Return ONLY ONE intent.

If uncertain,

return UNKNOWN.

--------------------------------------------------

Return JSON ONLY.

Example

{{
    "intent":"DECISION",
    "confidence":0.98
}}

Never explain your reasoning.

Never answer the user.

--------------------------------------------------

Conversation History

{history}

--------------------------------------------------

Current User Query

{current_query}

"""

    return prompt


if __name__ == "__main__":

    history = [

        {
            "role": "user",
            "message": "Why was this applicant rejected?"
        },

        {
            "role": "assistant",
            "message": "The DTI ratio exceeded policy."
        }

    ]

    prompt = build_routing_prompt(

        conversation_history=history,

        current_query="What if income becomes 80000?",

    )

    print(prompt)