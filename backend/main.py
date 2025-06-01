from fastapi import FastAPI, UploadFile, Response, status
from .scripts.get_tiktok_metadata import save_new_tiktok_metadata_video
from pydantic import BaseModel
import json
from backend.scripts.analyze_tiktok import analyze_tiktok_descriptions

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


##############################
######### USER ###############
##############################
class UserData(BaseModel):
    id: int
    name: str | None
    age: int  | None
    email: str | None
    phone: str | None
    address: str | None

@app.post("/api/v0/user/upload/infos", status_code=status.HTTP_200_OK, tags=["user"])
async def upload_user_info(user_data: UserData):
    # Convert the Pydantic model to a dictionary
    user_data_dict = user_data.model_dump()
    # Convert the dictionary to a JSON string
    user_data_json = json.dumps(user_data_dict)
    # Save the JSON string to a file
    try:
        with open("resources/user_info/user_data.json", "r+", encoding="utf-8") as f:
            try:
                users_data = json.load(f)
            except json.JSONDecodeError:
                users_data = {"users": []}  # Initialize if file is empty or invalid
            users_data['users'].append(user_data_dict)
            f.seek(0)
            json.dump(users_data, f, indent=4)
            f.truncate()
    except FileNotFoundError:
        with open("resources/user_info/user_data.json", "w", encoding="utf-8") as f:
            users_data = {"users": [user_data_dict]}
            json.dump(users_data, f, indent=4)
    return {"message": "User data saved successfully"}


@app.post("/api/v0/user/upload/data", tags=["user"])
async def upload_user_data(file: UploadFile, id: int, response: Response, status_code=status.HTTP_200_OK):
    file_content = await file.read()  # Read the file content
    file_path = f"resources/user_data/{file.filename}".replace(".json", f"_{id}.json")  # Define the file path
    try:
        with open(file_path, "x", encoding='utf-8') as f:
            f.write(file_content.decode('utf-8'))  # Decode bytes to string and write to file
            response.status_code = status.HTTP_201_CREATED
        return {"id": id, "filename": file.filename, "message": "File uploaded successfully"}
    except FileExistsError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"id": id, "filename": file.filename, "message": "File already exists"}
    

@app.get("api/v0/user/tiktok/data", status_code=status.HTTP_200_OK, tags=["user","tiktok"])
async def get_user_data(id: int, response: Response):
    file_path = f'resources/user_data/tiktok/user_data_tiktok_{id}.json'
    print(file_path)
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            user_data = json.load(f)
            response.status_code = status.HTTP_200_OK
            return user_data
    except FileNotFoundError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "File not found"}
    except json.JSONDecodeError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "Error decoding JSON"}
    
@app.get("/api/v0/user/tiktok/following", status_code=status.HTTP_200_OK, tags=["user","tiktok"])
async def get_user_following(id: int, response: Response):
    user_data = await get_user_data(id, response)
    following_list = []
    try:
        result = user_data.get("Profile And Settings").get("Following").get("Following")
        for follow in result:
            following_list.append(f"https://www.tiktok.com/@{follow.get('UserName')}")
    except AttributeError:
        result = user_data.get("Your Activity").get("Following").get("Following")
        for follow in result:
            following_list.append(f"https://www.tiktok.com/@{follow.get('UserName')}")
        return following_list
    if not result:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "No following data found"}
    return following_list

@app.get("/api/v0/user/tiktok/likes", status_code=status.HTTP_200_OK, tags=["user","tiktok"])
async def get_user_like_list(id: int, response: Response):
    user_data = await get_user_data(id, response)
    like_list = []
    result = user_data.get("Your Activity").get("Like List").get("ItemFavoriteList")
    for like in result:
        like_list.append(like.get("link"))
    if not result:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "No likes data found"}
    return like_list


    
############################
######### TikTok ###########
############################
@app.get("/api/v0/tiktok/update", status_code=status.HTTP_200_OK, tags=["tiktok"])
async def update_tiktok_metadata(filename: str, response: Response):
    try:
        save_new_tiktok_metadata_video(filename)
    except FileNotFoundError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Error decoding JSON"}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}
    return {"message": "Metadata updated successfully"}


@app.get("/api/v0/tiktok/metadata", status_code=status.HTTP_200_OK, tags=["tiktok"])
async def get_all_tiktok_metadata(response: Response):
    path = 'resources/tiktok_video/tiktok_metadata.json'
    try:
        with open(path, 'r') as file:
            tiktok_metadata = json.load(file)
    except FileNotFoundError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Error decoding JSON"}
    metadata = tiktok_metadata["metadata"]
    return metadata
    
@app.get("/api/v0/tiktok/link/metadata", status_code=status.HTTP_200_OK, tags=["tiktok"])
async def get_tiktok_link(link: str,response: Response):
    tiktok_metadata = await get_all_tiktok_metadata(response)
    metadata = tiktok_metadata.get(link)
    if metadata:
        return metadata
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Link not found"}

@app.get("/api/v0/tiktok/analyze", status_code=status.HTTP_200_OK, tags=["tiktok"])
async def analyze_tiktok():
    return analyze_tiktok_descriptions("backend/resources/tiktok_video/tiktok_metadata.json")