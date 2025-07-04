from typing import List

from ..brain.brain import Brain
from ..logger import logger
from ..processor.splitter import Chunk


class NexusRAG:
    """
    The NexusRAG class orchestrates the Retrieval-Augmented Generation pipeline.
    """

    def __init__(self, brain: Brain):
        """
        Initializes the RAG pipeline.

        :param brain: The Brain instance containing configuration and state.
        """
        self.brain = brain

    def _generate_prompt(self, question: str, context_chunks: List[Chunk]) -> str:
        """
        Generates an augmented prompt for the LLM.
        """
        context = "\\n".join([chunk.content for chunk in context_chunks])
        prompt = f"""Based on the following context:
---
{context}
---

Please answer the question: {question}"""
        return prompt

    def generate_answer(self, question: str) -> str:
        """
        Executes the full RAG pipeline to generate an answer.
        """
        logger.info(f"Generating answer for question: {question}")

        # a. Retrieve relevant chunks
        if not self.brain.vector_store:
            logger.error("Vector store not initialized in Brain.")
            raise ValueError("Vector store not initialized in Brain.")

        logger.debug("Performing similarity search...")
        retrieved_chunks = self.brain.vector_store.similarity_search(query=question)

        context_chunk_ids = [str(chunk.document_id) for chunk in retrieved_chunks]
        logger.info(
            f"Retrieved {len(retrieved_chunks)} chunks with document IDs: "
            f"{context_chunk_ids}"
        )

        # b. Augment the prompt
        prompt = self._generate_prompt(question, retrieved_chunks)
        messages = [{"role": "user", "content": prompt}]

        # c. Generate the answer using the LLM
        if not self.brain.llm_endpoint:
            logger.error("LLM endpoint not initialized in Brain.")
            raise ValueError("LLM endpoint not initialized in Brain.")

        logger.debug("Calling LLM to generate final answer...")
        answer = self.brain.llm_endpoint.get_chat_completion(messages)
        logger.info(f"Generated answer: {answer}")

        # d. Update history
        self.brain.history.append({"user": question, "assistant": answer})

        return answer
