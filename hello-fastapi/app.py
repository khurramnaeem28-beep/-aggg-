from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Hello FastAPI")


@app.get("/")
def root():
    return {"message": "Hello from FastAPI!"}


@app.get("/greet/{name}")
def greet(name: str, loud: bool = False):
    """Path param (name) + query param (loud, defaults to False)."""
    greeting = f"Hello, {name}!"
    return {"greeting": greeting.upper() if loud else greeting}


class Item(BaseModel):
    title: str
    done: bool = False


@app.post("/items")
def create_item(item: Item):
    """FastAPI validates the JSON body against Item before this runs."""
    return {"received": item}
