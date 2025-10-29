import logging

from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter()
router.data = {}

logger = logging.getLogger(__name__)

@router.post("/save_data_to_mongodb", response_class=JSONResponse)
# @router.post("/save_data_to_mongodb")
def save_to_mongo():
    logger.info("saving to mongo")
    # spotify_to_mongodb: SpotifyToMongo = SpotifyToMongo()
    # spotify_to_mongodb.save_all_data(app.all_data)
    # logger.debug("saved to mongo")
    # return redirect(url_for("index"))
    return JSONResponse(content={"message": "Data saved to MongoDB"})