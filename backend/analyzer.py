import os
import re
import json
import asyncio
from collections import defaultdict
from datetime import datetime, timezone 

import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from github import Github

from github.GithubException import UnknownObjectException, RateLimitExceededException
from openai import AsyncOpenAI 

from dotenv import load_dotenv
load_dotenv()

# first-time setup for NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

# --- config OpenAI API ---
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("⚠️ Warning: OPENAI_API_KEY not found. AI review will be skipped.")
    client = None
else:
    client = AsyncOpenAI(api_key=api_key)


class RepoAnalyzer:
    MAX_PRS_TO_ANALYZE = 25
    MAX_COMMITS_TO_ANALYZE = 100
    MODIFICATION_WEIGHT = 0.6
    AUTHOR_WEIGHT = 0.4

    def __init__(self, repo_url: str):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub Token not found in .env file!")
        
        self.g = Github(self.github_token)
        
        match = re.search(r"github\.com/([^/]+/[^/]+)", repo_url)
        if not match:
            raise ValueError("Invalid GitHub repository URL")
        self.repo_name = match.group(1)
        
        try:
            self.repo = self.g.get_repo(self.repo_name)
        except UnknownObjectException:
            raise ValueError(f"Repository '{self.repo_name}' not found or it's private.")
        
    # use for AI code review
    async def _review_one_file_async(self, filename: str):
        print(f"Starting AI review for {filename}...")
        try:
            content_file = self.repo.get_contents(filename)
            
            if content_file.size > 1_000_000: # 1MB limit
                return {"filename": filename, "code": "# File is too large.", "review": [], "error": "File exceeds 1MB and was not reviewed."}

            code = content_file.decoded_content.decode('utf-8')

            if not client:
                return {"filename": filename, "code": code, "review": [], "error": "OpenAI API Key not configured."}
            
            # --- FIX 1: Make the prompt align with the response_format parameter ---
            # We are now explicitly asking for a JSON object with an "issues" key.
            prompt = """
            You are an expert Senior Software Engineer. Your task is to perform a strict code review.

            # INSTRUCTIONS
            Analyze the provided code. For each issue found, provide a JSON object with the following fields:
            1.  `line_number`: The specific line number where the issue occurs.
            2.  `code_snippet`: The exact, unmodified line of code where the issue occurs.
            3.  `issue_type`: A category like "Potential Bug", "Security", "Code Quality", "Performance".
            4.  `description`: A concise explanation of the issue.
            5.  `suggestion`: A concrete suggestion on how to fix the code.

            # OUTPUT FORMAT
            Your final output must be a single JSON object with one key: "issues".
            The value of "issues" must be an array of the issue objects you found.
            If no issues are found, the "issues" array must be empty.
            Example: {"issues": [{"line_number": 42, "code_snippet": "let x = y * 2;", ...}]}
            Do NOT include any other text, explanations, or markdown.
            """

            completion = await client.chat.completions.create(
                model="gpt-4.1", 
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"# CODE TO REVIEW\n---\n{code}"}
                ],
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            if not response_content:
                return {"filename": filename, "code": code, "review": [], "error": "AI returned an empty response."}

            # --- FIX 3: Simplify the parsing logic to be direct and clear ---
            # No more guessing. We expect a specific format and handle it.
            try:
                data = json.loads(response_content)
                # Directly access the "issues" key. If it's not a list, it's an error.
                if isinstance(data, dict) and isinstance(data.get("issues"), list):
                    review_result = data["issues"]
                else:
                    # This handles cases where the structure is wrong, even if it's valid JSON.
                    raise ValueError("The response JSON object does not contain a valid 'issues' list.")

                return {"filename": filename, "code": code, "review": review_result, "error": None}

            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse AI response for {filename}. Error: {e}")
                print(f"Raw response was: {response_content}")
                return {"filename": filename, "code": code, "review": [], "error": f"AI returned an invalid data structure. Details: {e}"}
            
        except RateLimitExceededException as e:
            # This is a GitHub API exception, not OpenAI's
            return {"filename": filename, "code": "# Could not fetch content.", "review": [], "error": f"GitHub API rate limit exceeded: {e}"}
        except Exception as e:
            print(f"An unexpected error occurred during review for {filename}: {e}")
            return {"filename": filename, "code": "# Could not fetch file content.", "review": [], "error": str(e)}

    # analyze collaboration metrics like PR merge times and review comments
    def _analyze_collaboration(self):
        print("Analyzing collaboration metrics...")
        try:
            pulls = self.repo.get_pulls(state='closed', sort='updated', direction='desc')
            
            total_review_comments = 0
            total_merge_duration_seconds = 0
            merged_pr_count = 0
            
            # analyze up to 25 merged PRs
            for pr in pulls:
                if merged_pr_count >= self.MAX_PRS_TO_ANALYZE:
                    break
                if pr.merged:
                    merged_pr_count += 1
                    if pr.merged_at and pr.created_at:
                        merge_duration = pr.merged_at - pr.created_at
                        total_merge_duration_seconds += merge_duration.total_seconds()
                    total_review_comments += pr.review_comments
            
            avg_merge_seconds = total_merge_duration_seconds / merged_pr_count if merged_pr_count > 0 else 0
            avg_review_comments = total_review_comments / merged_pr_count if merged_pr_count > 0 else 0

            hours, remainder = divmod(avg_merge_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            return {
                "avg_merge_time_str": f"{int(hours)}h {int(minutes)}m" if avg_merge_seconds > 0 else "N/A",
                "avg_review_comments": round(avg_review_comments, 2)
            }
        except Exception as e:
            print(f"Could not analyze collaboration metrics: {e}")
            return {
                "avg_merge_time_str": "N/A",
                "avg_review_comments": "N/A"
            }

    # main method to perform full analysis
    async def analyze_full(self):
        print(f"Starting FULL analysis for {self.repo_name}...")

        # 1. Macro Analysis
        commits = self.repo.get_commits()
        file_modifications = defaultdict(int)
        file_authors = defaultdict(set)
        tech_debt_keywords = ["fixme", "todo", "hack", "xxx"]
        tech_debt_count = 0
        total_commits_analyzed = 0

        # analyze the most recent 100 commits
        for commit in commits[:self.MAX_COMMITS_TO_ANALYZE]:
            total_commits_analyzed += 1
            author = commit.author.login if commit.author else "unknown_author"
            
            message = commit.commit.message.lower()
            tokens = word_tokenize(message)
            for keyword in tech_debt_keywords:
                if keyword in tokens:
                    tech_debt_count += 1

            if commit.files:
                for file in commit.files:
                    filename = file.filename
                    file_modifications[filename] += 1
                    file_authors[filename].add(author)
        
        df = pd.DataFrame({
            'filename': list(file_modifications.keys()),
            'modifications': [file_modifications[f] for f in file_modifications.keys()],
            'authors_count': [len(file_authors[f]) for f in file_modifications.keys()]
        })

        if df.empty:
             return {
                "repo_info": {"name": self.repo_name, "stars": 0, "forks": 0, "open_issues": 0},
                "metrics": {"tech_debt_index": 0, "avg_merge_time_str": "N/A", "avg_review_comments": 0},
                "bug_hotbeds": [],
                "ai_reviews": []
            }
        
        # risk_score = (modifications * 0.6) + (authors_count * 0.4)
        df['risk_score'] = (df['modifications'] * self.MODIFICATION_WEIGHT) + (df['authors_count'] * self.AUTHOR_WEIGHT)
        if df['risk_score'].max() > 0:
            df['risk_score'] = (df['risk_score'] / df['risk_score'].max()) * 100
        
        df = df.sort_values(by='risk_score', ascending=False).round(2)
        
        tech_debt_index = (tech_debt_count / total_commits_analyzed) * 100 if total_commits_analyzed > 0 else 0
        bug_hotbeds = df.head(10).to_dict('records')

        # 2. Collaboration Metrics Analysis
        collaboration_metrics = self._analyze_collaboration()

        # 3. Automated Concurrent AI Code Review (Top 3 Files)
        top_files_to_review = [file['filename'] for file in bug_hotbeds[:3]]
        
        review_tasks = [self._review_one_file_async(filename) for filename in top_files_to_review]
        ai_reviews = await asyncio.gather(*review_tasks)

        # 4. Combine all results into a JSON
        final_result = {
            "repo_info": {
                "name": self.repo_name,
                "stars": self.repo.stargazers_count,
                "forks": self.repo.forks_count,
                "open_issues": self.repo.open_issues_count
            },
            "metrics": {
                "tech_debt_index": round(tech_debt_index, 2),
                **collaboration_metrics 
            },
            "bug_hotbeds": bug_hotbeds,
            "ai_reviews": ai_reviews
        }

        print("Full analysis complete.")
        return final_result