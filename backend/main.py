from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import traceback

from analyzer import RepoAnalyzer

load_dotenv()
app = FastAPI()

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
    receive a GitHub repository URL and perform a full macro and micro analysis.
    This is a longer-running request.
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
