# Python Data Streams
Manipulate pickled Python objects through shell pipes

# What it is
pds is a command-line tool to create python-based pipelines in the shell. It comes in handy if you are more of a 
Python expert than a shell expert, and can replace complex shell scripts and/or pipelines (grep, sed, awk, tr, sort...) 
with more readable (but also more wordy) commands.

The main differences compared to other "python code in the command line" tools such as pyp, pyped are:
1. Python objects are sent directly through the pipelines instead of text representations
    * this is more convenient and allows for longer, more complex pipelines as there is no need to convert back and
      forth between objects and text
    * it is also safer as there is less need to deal with quirks of textual representation (splitting, whitespace and
      quoting etc.)
2. Lots of built-in "modes" (commands) require less typing and lead to more concise command lines




