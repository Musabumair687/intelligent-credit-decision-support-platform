"""
intent_schema.py

Purpose
-------
Defines all supported user intents for the
Decision Intelligence module.

The Intent Router classifies every incoming
user query into one of these predefined intents.

These intents are later used by the
Orchestrator to decide which pipeline
should be executed.

Supported Intents
-----------------
GENERAL
    General conversation.

DECISION
    Loan prediction explanation.

KNOWLEDGE
    Bank policy / RAG questions.

SIMULATION
    What-if analysis.

UNKNOWN
    Fallback intent.

Author
------
Intelligent Credit Decision Support Platform
"""

from enum import Enum


class Intent(Enum):
    """
    Supported system intents.
    """

    GENERAL = "GENERAL"

    DECISION = "DECISION"

    KNOWLEDGE = "KNOWLEDGE"

    SIMULATION = "SIMULATION"

    UNKNOWN = "UNKNOWN"


if __name__ == "__main__":

    print("=" * 60)
    print("SUPPORTED INTENTS")
    print("=" * 60)

    for intent in Intent:

        print(intent.name, "->", intent.value)