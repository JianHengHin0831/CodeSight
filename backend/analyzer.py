# backend/analyzer.py

import os
from github import Github
from github.GithubException import UnknownObjectException
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from collections import defaultdict
import re

# 首次运行时需要下载 NLTK 数据
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.downloader.download('punkt')

class RepoAnalyzer:
    def __init__(self, repo_url: str):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub Token not found in .env file!")
        
        self.g = Github(self.github_token)
        
        # 从 URL 中解析仓库名称，例如 "https://github.com/vuejs/vue" -> "vuejs/vue"
        match = re.search(r"github\.com/([^/]+/[^/]+)", repo_url)
        if not match:
            raise ValueError("Invalid GitHub repository URL")
        self.repo_name = match.group(1)
        
        try:
            self.repo = self.g.get_repo(self.repo_name)
        except UnknownObjectException:
            raise ValueError(f"Repository '{self.repo_name}' not found or it's private.")

    def analyze(self):
        print(f"Starting analysis for {self.repo_name}...")
        
        commits = self.repo.get_commits()
        
        file_modifications = defaultdict(int)
        file_authors = defaultdict(set)
        tech_debt_keywords = ["fixme", "todo", "hack"]
        tech_debt_count = 0
        total_commits = 0

        # 为了性能，我们只分析最近的 100 个 commit
        for commit in commits[:100]:
            total_commits += 1
            author = commit.author.login if commit.author else "unknown"
            
            # 1. 分析提交信息中的技术债
            message = commit.commit.message.lower()
            tokens = word_tokenize(message)
            for keyword in tech_debt_keywords:
                if keyword in tokens:
                    tech_debt_count += 1

            # 2. 统计文件修改次数和参与者
            for file in commit.files:
                filename = file.filename
                file_modifications[filename] += 1
                file_authors[filename].add(author)
        
        print(f"Analyzed {total_commits} commits.")

        # 3. 创建 DataFrame 并计算风险分数
        df = pd.DataFrame({
            'filename': list(file_modifications.keys()),
            'modifications': [file_modifications[f] for f in file_modifications.keys()],
            'authors_count': [len(file_authors[f]) for f in file_modifications.keys()]
        })

        # 定义简单的风险评分算法 (权重可以调整)
        # 暂时忽略关联 Bug 数，简化 MVP
        df['risk_score'] = (df['modifications'] * 0.6) + (df['authors_count'] * 0.4)
        
        # 标准化分数到 0-100
        if not df.empty and df['risk_score'].max() > 0:
            df['risk_score'] = (df['risk_score'] / df['risk_score'].max()) * 100
        
        df = df.sort_values(by='risk_score', ascending=False).round(2)
        
        # 4. 计算技术债指数
        tech_debt_index = (tech_debt_count / total_commits) * 100 if total_commits > 0 else 0
        
        print("Analysis complete.")

        return {
            "repo_name": self.repo_name,
            "bug_hotbeds": df.head(10).to_dict('records'), # 返回风险最高的10个文件
            "tech_debt_index": round(tech_debt_index, 2)
        }