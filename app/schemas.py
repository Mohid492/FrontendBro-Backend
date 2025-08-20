from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class GoogleUser(BaseModel):
    sub: str
    email: str
    name: str
    picture: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChatData(BaseModel):
    session_id: str
    user_id: int
    prompt: str
    response: str

class ChatDataResponse(BaseModel):
    session_id: str
    prompt: str
    response: str


