"""
认证相关数据模式
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名至少需要3个字符')
        if len(v) > 50:
            raise ValueError('用户名不能超过50个字符')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        return v

class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse
