from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes import graph_router

app = FastAPI(
    title="DAG Graph Service",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

# CORS — если будешь использовать фронтенд или Postman
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Лучше указать конкретные домены на проде
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер с префиксом /api
app.include_router(graph_router, prefix="/api")

# Для запуска из терминала: `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
