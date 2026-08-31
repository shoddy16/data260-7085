# AI Use Disclosure

## 1. What AI was used for and what I did myself

I used an AI assistant to troubleshoot Python and LangChain/Ollama errors, organize the implementation steps, review code and organize the final documentation.

I personally created and maintained the project files, ran the commands locally, configured the Python environment and Ollama setup, executed the experiments, collected the console outputs and screenshots and verified the resulting files and measurements.

## 2. One AI-produced output that was wrong or unsuitable

During the AGENT.md code-review verification the model incorrectly stated that an empty string passed to the greet() function could cause an IndexError. The actual code would print "Hello " for an empty string; None would be more likely to cause a TypeError.

## 3. How the problem was detected

I checked the generated review against the actual submitted code instead of assuming that the model's explanation was correct. Examining the function showed that it did not index into the string so an empty string would not produce an IndexError.

## 4. What was changed and why

The incorrect claim was not used as a factual conclusion in the final analysis. The review output was treated as model generated evidence that still required human verification. This change makes the documentation more accurate because the behavior is based on the actual Python code rather than an unsupported model claim.