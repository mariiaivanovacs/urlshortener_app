from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Микросервис для сокращения ссылок",
    description="Microservice for shortening URLs/Микросервис для сокращения URL",
    version="1.0",
)

app.include_router(router)


# standard health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}
