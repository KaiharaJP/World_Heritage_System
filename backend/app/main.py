from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes.quiz import router as quiz_router

app = FastAPI(title="World Heritage Backend")

# 開発中は緩めの CORS 設定（必要に応じてホワイトリスト化）
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# 静的配信: /images -> /app/data/images (compose でマウント済み)
app.mount("/images", StaticFiles(directory="data/images"), name="images")

app.include_router(quiz_router)


@app.get("/")
def read_root():
	return {"message": "Backend is running"}


@app.get("/health")
def health_check():
	return {"status": "ok"}
