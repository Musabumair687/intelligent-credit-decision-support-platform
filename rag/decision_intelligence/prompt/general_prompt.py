"""
general_prompt.py

Purpose
-------
Builds the prompt for general banking
knowledge questions.

This prompt is used only when the user
asks questions regarding bank policies,
loan policies, regulations, compliance,
credit risk or any information stored
inside the RAG knowledge base.

This prompt DOES NOT use prediction
results or simulation context.

Author
------
Intelligent Credit Decision Support Platform
"""


from typing import List


def build_general_prompt(
    query: str,
    retrieved_documents: List[str],
):
    """
    Build the General RAG prompt.

    Parameters
    ----------
    query : str

    retrieved_documents : List[str]

    Returns
    -------
    str
        Prompt sent to the LLM.
    """

    documents = ""

    for index, document in enumerate(
        retrieved_documents,
        start=1,
    ):

        documents += (
            f"\nDocument {index}\n"
            f"{'-'*60}\n"
            f"{document}\n"
        )

    prompt = f"""
You are an experienced AI Banking Assistant
working for Stratum Capital Bank.

Your primary responsibility is to answer
questions using ONLY the information
provided in the retrieved bank documents.

--------------------------------------------------

Instructions

1. Answer only from the retrieved documents.

2. Do NOT invent information.

3. If the retrieved documents do not
contain enough information, clearly state

"I could not find sufficient information
inside the bank policy documents."

4. Give concise but complete answers.

5. When multiple documents discuss the
same topic, combine the information into
one coherent response.

6. Maintain a professional banking tone.

7. Do NOT mention internal document IDs
or chunk numbers.

--------------------------------------------------

Retrieved Documents

{documents}

--------------------------------------------------

User Question

{query}

--------------------------------------------------

Answer
"""

    return prompt


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    docs = [

        "Debt-to-Income Ratio should remain below 35 percent for standard consumer loans.",

        "Income verification is mandatory before loan approval.",

        "Applicants with unstable employment history require additional verification.",

    ]

    prompt = build_general_prompt(

        query="What is the DTI policy?",

        retrieved_documents=docs,

    )

    print("=" * 80)
    print("GENERAL PROMPT")
    print("=" * 80)

    print(prompt)