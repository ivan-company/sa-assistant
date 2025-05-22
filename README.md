# StackAdapt AI Assistant

This agent is meant to provide all the tools you may need for your day-to-day work


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

## Cursor integration

- Open the MCP settings (cmd+shift+P and search for "MCP")
- edit the configuration file
- Add the content of the file inside this project's `integrations/claude.json` in the config file

