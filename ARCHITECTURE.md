## Overview
This codebase is a command-line interface (CLI) tool designed to interact with language models for various programming tasks such as explaining, editing, fixing, and reviewing code. It provides a set of commands that can be invoked from the terminal.

## Modules
### cli.py
Handles the main entry point of the CLI tool, including version management, setup, and running individual commands.
Functions: version_callback, _setup, main, explain, review, edit, fix, find, describe, doctor

### commands/describe.py
Responsible for generating descriptions of code snippets using language models.
Functions: _build_prompt, run

### commands/edit.py
Manages the editing process by prompting the user and applying changes to the code.
Functions: run

### commands/explain.py
Explains code snippets to the user using natural language.
Functions: run

### commands/find.py
Searches for functions or patterns within code files.
Functions: _build_prompt, _parse_matches, run

### commands/fix.py
Automatically fixes issues in code snippets based on user input.
Functions: run

### commands/review.py
Reviews code snippets and provides feedback to the user.
Functions: run

### config.py
Manages configuration settings for the tool, including loading and merging configurations from files.
Functions: _load_toml, _merge, _global_config_path, _find_project_config, load_config

### context/extractor.py
Extracts functions and their offsets from code files in various programming languages.
Functions: detect_language, _get_name, _walk_python, _walk_javascript, _walk_go, _parse, _byte_offsets, extract_function, extract_function_with_offsets

### context/finder.py
Lists functions within code files and builds an index for efficient searching.
Functions: _list_python, _list_javascript, _list_go, list_functions_in_file, _walk_dir, index_directory

### context/limiter.py
Limits the number of tokens processed by language models to avoid exceeding usage limits.
Functions: __init__, estimate_tokens, check_limits

### context/reader.py
Reads code from files or standard input and handles different file formats.
Functions: read_file, read_stdin, read_code_string, read_function

### context/stack_parser.py
Parses error messages to identify the function causing an issue.
Functions: parse_error, find_function_at_line

### llm/client.py
Manages interactions with language models, including streaming responses and checking model availability.
Functions: stream_chat, check_model_available

### llm/prompts.py
Generates prompts for different types of tasks such as explaining, reviewing, editing, and fixing code.
Functions: explain_user, review_user, edit_user, fix_user

### output/diff.py
Handles the display of differences between original and modified code snippets.
Functions: strip_model_fences, make_unified_diff, has_changes, display_diff, display_no_changes, confirm_apply, splice_edit, apply_edit

### output/stream.py
Streams output to the user in a human-readable format, including plain text, review feedback, and error messages.
Functions: stream_plain, stream_review, print_token_warning, print_error, print_info

### runtime/hardware.py
Detects hardware capabilities of the system and provides recommendations based on the detected resources.
Functions: _recommend, detect_hardware, print_hardware_report