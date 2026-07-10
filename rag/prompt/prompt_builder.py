"""
prompt_builder.py

Purpose
-------
Convert retrieved documents into a single prompt
that will be sent to Gemini.
"""


class PromptBuilder:
    """
    Builds prompts for Gemini.
    """

    def __init__(self):

        self.system_prompt = """
You are an expert AI Banking Assistant.

Your job is to answer ONLY using the supplied banking policy documents.

Rules:

1. Never make up information.

2. If the answer is not found in the provided context,
   say:

   "I couldn't find sufficient information in the provided banking policies."

3. Quote policy information whenever possible.

4. Keep answers clear and professional.

5. Do not mention information outside the supplied documents.
"""

    def build_prompt(
        self,
        question: str,
        documents: list,
    ) -> str:
        """
        Build final prompt.

        Parameters
        ----------
        question : str

        documents : list[Document]

        Returns
        -------
        str
        """

        context = ""

        for i, doc in enumerate(documents, start=1):

            page = doc.metadata.get("page_label", "Unknown")

            source = doc.metadata.get("source", "Unknown")

            context += f"""
==============================
Document {i}

Source:
{source}

Page:
{page}

Content:
{doc.page_content}

"""

        prompt = f"""
{self.system_prompt}

=================================================

BANKING POLICY CONTEXT

{context}

=================================================

QUESTION

{question}

=================================================

ANSWER
"""

        return prompt

