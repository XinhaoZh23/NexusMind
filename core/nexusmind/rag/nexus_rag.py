from typing import List
from core.nexusmind.brain.brain import Brain
from core.nexusmind.processor.splitter import Chunk


class NexusRAG:
    """
    The NexusRAG class orchestrates the Retrieval-Augmented Generation pipeline.
    """

    def __init__(self, brain: Brain, knowledge_base: List[Chunk] = None):
        """
        Initializes the RAG pipeline.

        :param brain: The Brain instance containing configuration and state.
        :param knowledge_base: A list of Chunks to serve as the knowledge base.
        """
        self.brain = brain
        self.knowledge_base = knowledge_base or []

    def _retrieve(self, question: str) -> List[Chunk]:
        """
        A pseudo-retrieval step.
        For now, it returns the first 3 chunks from the knowledge base.
        A real implementation would use a vector database.
        """
        # Simple keyword matching for a slightly better mock retrieval
        question_keywords = set(question.lower().split())
        
        # Score chunks based on keyword overlap
        scored_chunks = []
        for chunk in self.knowledge_base:
            chunk_keywords = set(chunk.content.lower().split())
            score = len(question_keywords.intersection(chunk_keywords))
            if score > 0:
                scored_chunks.append((score, chunk))

        # Sort by score and return top chunks
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Return the actual Chunk objects
        top_chunks = [chunk for score, chunk in scored_chunks[:3]]
        
        return top_chunks

    def _generate_prompt(self, question: str, context_chunks: List[Chunk]) -> str:
        """
        Generates an augmented prompt for the LLM.
        """
        context = "\n".join([chunk.content for chunk in context_chunks])
        prompt = (
            f"Based on the following context:\n---
\n"
            f"{context}\n---
\n\n"
            f"Please answer the question: {question}"
        )
        return prompt

    def generate_answer(self, question: str) -> str:
        """
        Executes the full RAG pipeline to generate an answer.
        """
        # a. Retrieve relevant chunks
        retrieved_chunks = self._retrieve(question)

        # b. Augment the prompt
        prompt = self._generate_prompt(question, retrieved_chunks)
        messages = [{"role": "user", "content": prompt}]

        # c. Generate the answer using the LLM
        if not self.brain.llm_endpoint:
             raise ValueError("LLM endpoint not initialized in Brain.")
        answer = self.brain.llm_endpoint.get_chat_completion(messages)

        # d. Update history
        self.brain.history.append({"user": question, "assistant": answer})
        
        return answer 