from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "It works!"}

@app.get("/status")
def status():
    return {"status": "healthy"}
