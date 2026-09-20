 <!-- AI Use
 
1 What did you use an AI assistant for?
I used an AI assistant mainly to understand the assignment requirements, debug Python/FastAPI issues, check PowerShell commands and to organize the report sections.

2 One incorrect/unsuitable AI output or independent verification
The AI suggested checking the corpus using:
Get-ChildItem reports\hw03\corpus -File | Measure-Object Length -Sum

3 How did you detect/verify it?
I ran the command from the Homeworks directory instead of the data260-7085 repository directory, which produced a PathNotFound error. I then navigated to the correct repository and reran the command successfully. The corpus was confirmed to contain 9 files with a total size of 13,824,130 bytes. 


4 What did you change and why?
I changed the working directory before running the command and used the resulting output from the correct project location.
I made this change because the original command was being executed from the wrong directory. The AI's command itself was useful for checking the corpus but the context in which I ran it was wrong. I verified the issue myself, corrected the path, reran the command, and used only the successful result in my report. -->
