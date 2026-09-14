
# AI Use

## 1. What did you use an AI assistant for, and what did you do yourself?

I used an AI assistant mainly when I needed help understanding some HW2 requirements, debugging errors and checking my approach. I also used it for a few suggestions about the LangGraph structure and experiment setup. I did the implementation, ran the application and experiments, checked the results and created the final screenshots and report myself.

## 2. Give one AI-produced output that was wrong or unsuitable, or one thing you independently verified.

One thing I independently verified was the LangGraph validation and retry behavior. I ran the graph locally and tested an intentionally invalid Planner output to make sure the Reviewer rejected it and the graph went back to the Planner.

## 3. How did you detect the problem or verify the result?

I used the terminal output and the generated experiment files to verify the behavior. I checked the Planner and Reviewer states during the graph run and also checked the CSV results and METRICS.md after running the experiments.

## 4. What did you change, and why does it work now?

I fixed the issues I found during testing, including the Python import problem and the validation/retry flow. I then reran the graph and experiments. The graph completed successfully, the invalid-output test triggered a retry and the required experiments completed with the recorded results.