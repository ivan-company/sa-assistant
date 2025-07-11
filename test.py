import asyncio
import yaml
from agents import Runner, RunConfig
from sa_assistant.integrations.google.docs import GoogleDocsAPI
from sa_assistant.vectorstore.chroma_store import VectorStore
from sa_assistant.agents.daily_check import daily_calendar_check_agent
from sa_assistant.integrations.asana import AsanaAPI
from sa_assistant.utils import load_config_and_setup_env
from sa_assistant.context import AssistantContext
import sa_assistant

config, context = load_config_and_setup_env()

config = yaml.load(
    open("config.yaml"), Loader=yaml.Loader
)
context = AssistantContext(**config)


async def main():
    # Create RunConfig with the model from context - currently only used for model selection
    run_config = RunConfig(model=context.openai_model)

    result = await Runner.run(
        sa_assistant.jira_agent,
        "Help me summarize sprint goal for the 'GROW' project, in the current sprint.",
        context=context,
        run_config=run_config,
    )
    print(result.final_output)


async def test_daily_calendar_check():
    result = await Runner.run(
        daily_calendar_check_agent,
        "What is my calendar for next Monday?",
        context=context,
    )
    print(result.final_output)


async def test_asana():
    api = AsanaAPI(context.asana.api_token, context.asana.team_id)
    projects = api.get_projects_with_users(
        ["ivan.company@stack.com", "devon.mack@stack.com"])
    for project in projects:
        print(f"Project: {project.name}")
        tasks = api.get_tasks_by_project(project.gid)
        for task in tasks:
            print(f"Task: {task.name}")
            print(
                f"Assignee: {task.assignee.name if task.assignee else 'None'}")
            print(f"Notes: {task.notes}")
            print(
                f"Section: {task.section.name if task.section else 'None'}")
            print(f"Completed: {task.completed}")


async def test_vector_store():
    store = VectorStore()
    # Add sample documents
    docs = [
        {
            "id": "doc1",
            "text": "StackAdapt is a programmatic advertising platform.",
            "metadata": {"title": "About StackAdapt"}
        },
        {
            "id": "doc2",
            "text": (
                "Vector databases enable semantic search over large text corpora."
            ),
            "metadata": {"title": "Vector DBs"}
        },
        {
            "id": "doc3",
            "text": (
                "Confluence is used for documentation and knowledge sharing."
            ),
            "metadata": {"title": "Confluence"}
        },
    ]
    store.add_documents("test", docs)
    # Search
    query = "What is StackAdapt?"
    results = store.search(query, source="test", top_k=2)
    print("Search results for:", query)
    for res in results:
        print(
            f"ID: {res['id']}, Title: {res['metadata'].get('title')}, "
            f"Text: {res['text']}"
        )


async def _populate_vector_store():
    store = VectorStore()
    gdocs = GoogleDocsAPI()
    # PRD for "Generative AI V1: Creatives Builder"
    file_id = "10G2ztvu5cCOjgRShsuNCeqsuWxiyMG3Q1P9hDgkdxos"
    prd = gdocs.extract_data(file_id)
    # Store in vector DB

    for i, row in enumerate(prd):
        chunk_id = f"{file_id}_chunk_{i}"
        doc = {
            "id": chunk_id,
            "text": row,
            "metadata": {
                "document_id": chunk_id,
                "document_source": "prd",
                "document_title": "PRD: Generative AI V1: Creatives Builder",
            }
        }
        store.add_documents("gdrive", [doc])


async def test_gdocs_extraction():
    store = VectorStore()

    if not store.has_collection("gdrive"):
        await _populate_vector_store()

    # Query
    query = "What is the purpose of the Generative AI Creatives Builder?"
    results = store.search(query, source="gdrive", top_k=2)
    print("Search results for:", query)
    for res in results:
        print(
            f"ID: {res['id']}, Title: {res['metadata'].get('title')}, "
            f"Text: {res['text']}"
        )


async def test_slack_agent():
    """Test the slack agent by sending a test message"""
    run_config = RunConfig(model=context.openai_model)

    # Test sending a message to a channel (replace with your actual channel and prompts)
    result = await Runner.run(
        sa_assistant.slack_agent,
        "Send a test message 'Hello from the AI assistant!' to @Winston Zhu",
        context=context,
        run_config=run_config,
    )
    print("Slack test result:", result.final_output)


async def test_slack_agent_dm():
    """Test the slack agent by sending a DM"""
    run_config = RunConfig(model=context.openai_model)

    # Test sending a DM (replace with actual username)
    result = await Runner.run(
        sa_assistant.slack_agent,
        "Send a direct message 'Hi! This is a test from the AI assistant.' to @ivan.company",
        context=context,
        run_config=run_config,
    )
    print("Slack DM test result:", result.final_output)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "slack":
            asyncio.run(test_slack_agent())
        elif test_name == "slack-dm":
            asyncio.run(test_slack_agent_dm())
        elif test_name == "jira":
            asyncio.run(main())
        elif test_name == "gdocs":
            asyncio.run(test_gdocs_extraction())
        else:
            print("Available tests: slack, slack-dm, jira")
    else:
        # Default test
        asyncio.run(main())
