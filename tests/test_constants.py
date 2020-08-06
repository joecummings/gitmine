from pathlib import Path

TEST_GITHUB_CREDENTIALS_PATH = Path.home() / Path(".gitmine_credentials")
TEST_KEY_PATH = Path(__file__).parents[1] / Path("gitmine.key")

TEST_ISSUES_PATH = Path(__file__) / Path("data/issues.json")
TEST_PRS_PATH = Path(__file__) / Path("data/prs.json ")
