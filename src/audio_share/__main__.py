import uvicorn

from fastapi import FastAPI

from .route import router
from .curd import init_db

app = FastAPI()

app.include_router(router)


@app.on_event("startup")
async def startup():
    await init_db()


def run():
    uvicorn.run(app, host="0.0.0.0", port=8045)


if __name__ == "__main__":
    run()
