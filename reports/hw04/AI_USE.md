# AI Use.md

## 1. What did you use an AI assistant for, and what did you do yourself?

I used an AI assistant mainly for understanding the HW4 requirements and for debugging guidance.

## 2. What AI-produced output was wrong/unsuitable, or what did you independently verify?

I independently verified all the application behavior and experiment results instead of assuming that AI-suggested debugging advice is correct.

I also verified that the local implementation produced the expected database, N+1 benchmark, Chroma indexing, retrieval, and RAG evaluation outputs.

## 3. How did you detect the problem or verify the result?

I used the terminal output, generated experiment files, screenshots, and repository artifacts to verify the results. I ran the implementation locally and compared the observed outputs with the homework requirements.

For the RAG portion, I checked the retrieved source documents, chunk IDs, retrieval scores, generated answers, and refusal behavior. I also reviewed the saved raw results and report evidence after the experiments completed.

## 4. What did you change and why does it work now?

I fixed the implementation and configuration issues found during development and reran the affected experiments to confirm the results. I also organized the retrieved context and RAG evidence so that the Context-RAG configuration uses the provided course documents as its evidence source.

The final implementation successfully produced the required local outputs, including the database/N+1 experiments, document indexing, top-k retrieval results, No-RAG / Basic-RAG / Context-RAG comparison, and refusal behavior for unsupported questions. The final report uses the observed local outputs and screenshots as evidence.
