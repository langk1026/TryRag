import google.generativeai as genai
from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    def __init__(self):
        genai.configure(api_key=config.google_api_key)
        self.model = genai.GenerativeModel(config.llm_model)

    def generate_answer(self, question, context, temperature=0.7):
        prompt = f"""You are a helpful assistant that answers questions based on provided context.

Rules:
- Use only context facts
- If context is insufficient, say so clearly
- Cite document names where applicable
- Keep the answer concise and factual

Context:
{context}

Question: {question}
"""

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=1000
        )

        response = self.model.generate_content(prompt, generation_config=generation_config)
        answer = response.text or "I apologize, but I was unable to generate a response at this time."
        return answer

    def generate_hypothetical_answer(self, question):
        prompt = f"""You generate a hypothetical answer for HyDE retrieval.

Question: {question}
Generate a concise but information-rich hypothetical answer.
"""

        generation_config = genai.types.GenerationConfig(
            temperature=config.hyde_temperature,
            max_output_tokens=config.hyde_max_tokens
        )

        response = self.model.generate_content(prompt, generation_config=generation_config)
        return response.text or question
