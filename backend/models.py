from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    mobile: str

class LoginRequest(BaseModel):
    username: str
    password: str

class BehaviorRequest(BaseModel):
    user_id: str
    location: str
    device: str
    access_speed: float

class VerifyRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str