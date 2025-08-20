from fastapi import status,APIRouter,HTTPException
from app.RAG.vector_maker import vector_maker

router = APIRouter(
    prefix='/generate-vector',
    tags=['vector generator']
)

@router.post('/generate-vector', status_code=status.HTTP_200_OK)
async def generate_vector():
    """
    Endpoint to generate vectors from scraped documentation.
    """
    try:
        message=vector_maker()
        return {"message":message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
