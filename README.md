# StackAdapt AI Assistant

This agent is meant to provide all the tools you may need for your day-to-day work


## Installation

- Download and install [uv](https://docs.astral.sh/uv/)
- Synchronize your local virtual environment:
```python
uv sync
```

Once that's done, you now have to create a "config.yaml" file with the same structure as the provided "config.yaml.template" file, replacing the values

## Structure

- `sa_assistant` module: contains all the logic for the assistant
- `test.py`: Contains a simple example on how to use the assistant programatically
- `server.py`: file that gets called by the MCP clients

## Usage

### standalone

If you just want to test the assistant without any MCP client, just run:

```python
uv run test.py
```

### Claude integration

- Open your Claude Desktop client
- Go to Settings -> Developer -> Edit Config
- Add the content of the file inside this project's `integrations/claude.json` in the config file
- Restart the client

### Cursor integration

- Open the MCP settings (cmd+shift+P and search for "MCP")
- edit the configuration file
- Add the content of the file inside this project's `integrations/claude.json` in the config file

## Roadmap

In here I'll keep a list of the things that I want to implement, with no effective deadlines since this is a side project:

- Google Meets now provides a tool to transcribe video calls, where it explains what the conversation was about and also summarizes the action plans. I want to make an agent that would read over those transcriptions and create Asana tickets for me
- "Good morning" agent: it will give me an overview of what I have to think of today:
    - Review team's backlog and capacity
    - Prepare for meetings
    - Asana tasks deadlines
    - Emails
    - etc
- "Project expert" agent: when working on a project, there are usually several elements to consider:
    - Google Meet meetings
    - Confluence pages
    - Slack channels
Because of this, I want an agent that would gather all this information so I can ask it about anything related to it. I'm thinking about keeping a simple database for projects and the attached documents so the agent can consult them.
