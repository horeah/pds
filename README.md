# Python Data Streams
Manipulate pickled Python objects through shell pipes

# What it is
pds is a command-line tool to create python-based pipelines in the shell. It comes in handy if you are more of a 
Python expert than a shell expert, and can replace complex shell scripts and/or pipelines (grep, sed, awk, tr, sort...) 
with more readable (but also more wordy) commands.

The main differences compared to other "python code in the command line" tools such as pyp, pyped, pythonpy etc. are:
1. Python objects are sent directly through the pipelines instead of text
    * this is more robust, and reduces the need to deal with quirks of textual representation (encodings, whitespace and quoting etc.)
    * it is also more convenient, as object methods can be called directly
2. Lots of built-in "modes" (commands) require less typing and lead to more expressive command chains

# Examples
## Count non-empty lines in a file
```bash
# grep -cve "^\s*$" pds.py
cat pds.py | pds filter "x.strip()" | pds count
```

## Print the name and size of the 5 largest files in the current directory
```bash
# find . -type f -exec du -h {} + | sort -hr | head -n 5
pds files -R | pds filter "x.is_file()" | pds each "x, x.stat().st_size" | pds sort -r "x[1]" | pds iter "islice(it, 5")
```



