# backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import traceback

from analyzer import RepoAnalyzer

# load environment variables from .env file 
load_dotenv()

app = FastAPI()

# configure CORS middleware to allow frontend (http://localhost:3000) access
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
async def analyze_repository(request: RepoRequest):
    """
    接收 GitHub 仓库 URL, 执行完整的宏观和微观分析。
    这是一个耗时较长的请求。
    """
    try:
        analyzer = RepoAnalyzer(repo_url=request.url)
        # call the asynchronous full analysis method
        result = await analyzer.analyze_full()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")
