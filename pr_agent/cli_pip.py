from pr_agent import cli
from pr_agent.config_loader import get_settings
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    # print(os.getenv("GITHUB_TOKEN"))
    # print(os.getenv("OPENAI_API_KEY"))

    # Fill in the following values
    provider = "github"  # GitHub provider
    user_token = os.getenv("GITHUB_TOKEN")  # GitHub user token
    openai_key = os.getenv("OPENAI_API_KEY")  # OpenAI key
    pr_url = "https://github.com/dthajal1/docusaurus-doc-updater-X-turborepo/pull/1"  # PR URL, for example 'https://github.com/Codium-ai/pr-agent/pull/809'
    command = "/ask 'What is the purpose of this PR?'"  # Command to run (e.g. '/help', '/review', '/describe', '/ask "What is the purpose of this PR?"')

    # Setting the configurations
    get_settings().set("CONFIG.git_provider", provider)
    get_settings().set("openai.key", openai_key)
    get_settings().set("github.user_token", user_token)

    # Run the command. Feedback will appear in GitHub PR comments
    cli.run_command(pr_url, command)


if __name__ == '__main__':
    main()
