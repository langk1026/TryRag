from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class RagasEvaluator:
    def __init__(self):
        self.enabled = config.ragas_enabled
        self.faithfulness_threshold = config.faithfulness_threshold

    def _heuristic_score(self, answer, contexts):
        if not answer or not contexts:
            return 0.0

        normalized_answer = answer.lower()
        context_text = "\n".join(contexts).lower()
        answer_terms = [token for token in normalized_answer.split() if len(token) > 4]

        if not answer_terms:
            return 0.6

        grounded = sum(1 for token in answer_terms if token in context_text)
        return grounded / len(answer_terms)

    def evaluate(self, question, answer, contexts):
        score = None
        mode = 'heuristic'

        if self.enabled:
            try:
                # RAGAS integration may require custom LLM wrappers depending on deployment.
                # Keep this resilient: if runtime setup is incomplete, fallback remains active.
                from ragas import SingleTurnSample
                from ragas.metrics import faithfulness

                sample = SingleTurnSample(
                    user_input=question,
                    response=answer,
                    retrieved_contexts=contexts
                )
                score = float(faithfulness.single_turn_score(sample))
                mode = 'ragas'
            except Exception as e:
                logger.warning(f"RAGAS evaluation failed, using heuristic fallback: {str(e)}")

        if score is None:
            score = self._heuristic_score(answer, contexts)

        return {
            'faithfulness': score,
            'passed': score >= self.faithfulness_threshold,
            'threshold': self.faithfulness_threshold,
            'mode': mode
        }
