
# Feature folder structure
  - Each feature should have its own folder
  - Create a .windsurf/rules in each feature folder and
    define your interpretation of the requirements.
      - I know you don't have access to this.
          - Write them to another temp folder.
          - Write and execute a bash script to move them.

This way we can work on each feature independently of the whole project if necessary

Folder naming convention:
Keep folder names short and human readable.
Don't use multiple words.
All lowercase.

# History and end of prompt
    - I want you to always keep a record of our chat history in the chats folder
        - When you are done carrying out your instructions
        - Create a numbered file under chats directory with:
          - Comprehensive history of our chat including prompts and all your reasoning
    - Also create a relevant commit message and commit the changes using git
