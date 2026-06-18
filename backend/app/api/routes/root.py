from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/")
def read_root():
    return {"message": "Welcome to paprnav!"}
