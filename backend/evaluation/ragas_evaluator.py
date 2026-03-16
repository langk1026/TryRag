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

    def _relevance_score(self, question, contexts):
        """Check if retrieved contexts are relevant to the question."""
        if not question or not contexts:
            return 0.0
        q_terms = set(t.lower() for t in question.split() if len(t) > 3)
        if not q_terms:
            return 0.5
        context_text = "\n".join(contexts).lower()
        hits = sum(1 for t in q_terms if t in context_text)
        return hits / len(q_terms)

    def _completeness_score(self, answer):
        """Check if the answer is substantive (not just 'I don't know')."""
        if not answer:
            return 0.0
        low = answer.lower().strip()
        refusal_phrases = [
            "i don't know", "i cannot", "i'm not sure", "no information",
            "not enough context", "unable to", "i apologize",
        ]
        for phrase in refusal_phrases:
            if low.startswith(phrase) or phrase in low[:100]:
                return 0.3
        word_count = len(answer.split())
        if word_count < 10:
            return 0.5
        return min(1.0, word_count / 50)

    def evaluate(self, question, answer, contexts):
        faithfulness_score = None
        mode = 'heuristic'

        if self.enabled:
            try:
                from ragas import SingleTurnSample
                from ragas.metrics import faithfulness

                sample = SingleTurnSample(
                    user_input=question,
                    response=answer,
                    retrieved_contexts=contexts
                )
                faithfulness_score = float(faithfulness.single_turn_score(sample))
                mode = 'ragas'
            except Exception as e:
                logger.warning(f"RAGAS evaluation failed, using heuristic fallback: {str(e)}")

        if faithfulness_score is None:
            faithfulness_score = self._heuristic_score(answer, contexts)

        relevance = self._relevance_score(question, contexts)
        completeness = self._completeness_score(answer)

        # Weighted pass: faithfulness 50%, relevance 30%, completeness 20%
        combined = (faithfulness_score * 0.5) + (relevance * 0.3) + (completeness * 0.2)
        passed = combined >= self.faithfulness_threshold

        return {
            'faithfulness': faithfulness_score,
            'relevance': relevance,
            'completeness': completeness,
            'combined_score': round(combined, 3),
            'passed': passed,
            'threshold': self.faithfulness_threshold,
            'mode': mode
        }
