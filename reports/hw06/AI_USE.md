# AI Use

1. I used an AI assistant to understand the HW6 rubric, plan the MongoDB and file-memory architecture, draft tests, debug PowerShell commands, and review implementation details. I ran the commands, inspected the repository, and verified the outputs myself.

2. I independently verified the assistant-produced implementation because generated code can use incorrect APIs or claim behavior that has not run. In particular, I checked the HW5 tag and remote branch before editing and tested the deterministic memory and consolidation paths.

3. I detected problems by comparing actual Git output with the handover, running the baseline test suite, and checking each new test result and generated JSON/CSV file rather than trusting a proposed result.

4. I changed the implementation to use lazy MongoDB access and deterministic offline model/embedding doubles. This keeps live-service behavior available while making the required tests reproducible and honest when MongoDB or Ollama is unavailable.
