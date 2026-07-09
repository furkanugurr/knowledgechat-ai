# FastAPI Routing

## Path Operations

FastAPI connects an HTTP method and URL path to a Python function. A decorator
such as `@app.get("/items")` registers the function as a path operation. FastAPI
validates declared parameters and serializes the returned value into an HTTP
response.

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(item_id: int) -> dict[str, int]:
    return {"item_id": item_id}
```

In this example, `/items/42` converts `42` to an integer before calling the
function. Invalid values produce a validation response automatically.

## APIRouter

`APIRouter` groups related endpoints outside the application entry point. A
router can define tags, shared dependencies, or a path prefix. The application
includes it with `include_router`.

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")
```

Separating routers keeps HTTP concerns organized as an application grows.
Route functions should validate transport input, call application services,
and map known errors to appropriate HTTP responses. Business or provider logic
belongs outside the router.
