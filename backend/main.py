# backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from analyzer import RepoAnalyzer

# 加载 .env 文件中的环境变量
load_dotenv()

app = FastAPI()

# 配置 CORS 中间件, 允许前端(http://localhost:3000)访问
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepoRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "CodeSight API is running."}

@app.post("/analyze")
def analyze_repository(request: RepoRequest):
    try:
        analyzer = RepoAnalyzer(repo_url=request.url)
        result = analyzer.analyze()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 捕获其他潜在错误，例如 GitHub API 速率限制
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")