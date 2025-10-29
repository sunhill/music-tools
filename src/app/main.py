import logging
import sys
import time

from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from app.api.routes.albums import router as albums_router
from app.api.routes.artists import router as artists_router
from app.api.routes.genres import router as genres_router
from app.api.routes.playlist_creation import router as playlist_creation_router
from app.api.routes.playlists import router as playlists_router
from app.api.routes.tracks import router as tracks_router
from app.api.routes.save_data import router as save_data_router
from app.config import app

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(
    playlist_creation_router, prefix="/playlist_creation", tags=["playlist_creation"]
)
app.include_router(playlists_router, tags=["playlists"])
app.include_router(tracks_router, tags=["tracks"])
app.include_router(albums_router, tags=["albums"])
app.include_router(artists_router, tags=["artists"])
app.include_router(genres_router, tags=["genres"])
app.include_router(save_data_router, tags=["save_data"])
app.include_router(playlist_creation_router, tags=["playlist_creation"])
templates = Jinja2Templates(directory="src/app/templates")

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fastapi_app")
if not logger.hasHandlers():  # Prevent duplicate handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(f"⬆️ Request: {request.method} {request.url}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"⬇️ Response: {request.method} {request.url} - {response.status_code} - {process_time:.4f}s"
    )

    return response


@app.get("/callback")
async def callback(request: Request):
    # Extract the authorization code from the query parameters
    code = request.query_params.get("code")
    if code:
        # Process the authorization code (e.g., exchange it for an access token)
        return {"message": "Authorization code received", "code": code}
    return {"error": "No authorization code provided"}



@app.get("/test")
def app_test():
    logger.debug("test")
    return {"message": "It works!"}


# Dynamic HTML page for listing all routes
@app.get("/", response_class=HTMLResponse)
async def list_routes(request: Request):
    # Get all defined routes in the application
    routes = []
    for route in app.routes:
        if isinstance(route, Route):  # Filter only for Route type objects
            routes.append({"path": route.path, "name": route.name or route.path})

    routes.sort(key=lambda x: x["name"])

    # Render the HTML template and pass the list of routes
    return templates.TemplateResponse(
        "routes.html",
        {"request": request, "routes": routes},
        #
        # "routes.html", {"request": request, "routes": routes,"target_blank": True}
    )
