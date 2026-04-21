import re
from github import Github, Auth
from semanticscholar import SemanticScholar
from ..config import settings
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        # Initialize GitHub Client
        try:
            auth = Auth.Token(settings.github_token)
            self.gh = Github(auth=auth)
            logger.info("GitHub client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            self.gh = None

        # Initialize Semantic Scholar Client
        try:
            if settings.semantic_scholar_api_key:
                self.sch = SemanticScholar(api_key=settings.semantic_scholar_api_key)
            else:
                self.sch = SemanticScholar()
            logger.info("Semantic Scholar client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Semantic Scholar client: {e}")
            self.sch = None

    def parse_github_url(self, url: str):
        """Extract owner and repo name from GitHub URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if match:
            return match.group(1), match.group(2).replace(".git", "")
        return None, None

    def fetch_github_data(self, url: str):
        """Fetch repository metadata from GitHub."""
        if not self.gh:
            return None

        owner, repo_name = self.parse_github_url(url)
        if not owner or not repo_name:
            logger.error(f"Invalid GitHub URL: {url}")
            return None

        try:
            repo = self.gh.get_repo(f"{owner}/{repo_name}")
            
            # Basic metadata
            data = {
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "created_at": repo.created_at,
                "last_commit_date": repo.get_commits()[0].commit.committer.date,
                "readme_length": 0,
                "has_test_files": 0
            }

            # README content & length
            try:
                readme = repo.get_readme()
                content = readme.decoded_content.decode("utf-8")
                data["readme_length"] = len(content)
                data["readme_content"] = content[:1000] # Truncate for neural processing speed
            except:
                data["readme_content"] = ""

            # Check for test files (rough heuristic)
            try:
                contents = repo.get_contents("")
                for content_file in contents:
                    if "test" in content_file.name.lower():
                        data["has_test_files"] = 1
                        break
            except:
                pass

            # Contributors and Commits count (Disabled for speed in enterprise audits)
            data["contributors_count"] = 1 
            data["commits_count"] = 1 

            # Technical Stack (New Features)
            try:
                data["languages"] = list(repo.get_languages().keys())[:5]
                data["topics"] = repo.get_topics()[:5]
            except:
                data["languages"] = []
                data["topics"] = []

            return data
        except Exception as e:
            logger.error(f"Error fetching GitHub data for {url}: {e}")
            return None

    def fetch_scholar_data(self, query: str):
        """Search for a paper and return citation/author metrics."""
        if not self.sch:
            return None

        try:
            # Search for the paper by title/abstract (Guard against empty/short queries)
            if not query or len(query.strip()) < 10:
                return None
                
            results = self.sch.search_paper(query, limit=1)
            if not results:
                return None

            paper = results[0]
            
            # Author metrics
            authors_data = []
            for author in paper.authors:
                try:
                    # Fetch detailed author info including h-index
                    author_details = self.sch.get_author(author.authorId)
                    authors_data.append({
                        "name": author_details.name,
                        "h_index": getattr(author_details, "hIndex", 0),
                        "paper_count": getattr(author_details, "paperCount", 0)
                    })
                except:
                    authors_data.append({"name": author.name, "h_index": 0})

            return {
                "paper_title": paper.title,
                "citation_count": paper.citationCount,
                "authors": authors_data
            }
        except Exception as e:
            logger.error(f"Error fetching Semantic Scholar data for {query}: {e}")
            return None
