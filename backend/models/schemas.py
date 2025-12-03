from pydantic import BaseModel, Field
from typing import Optional, Literal

# ===== АВТОРИЗАЦИЯ =====

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

class LoginResponse(BaseModel):
    success: bool
    message: str
    ip: Optional[str] = None

class AuthCheckResponse(BaseModel):
    authorized: bool
    username: Optional[str] = None
    role: Optional[str] = None
    ip: Optional[str] = None

# ===== ПОЛЬЗОВАТЕЛИ =====

class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    role: Literal["admin", "user"] = "user"

class UserCreate(UserBase):
    password: str = Field(..., min_length=1, max_length=100)

class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[Literal["admin", "user"]] = None

class UserResponse(UserBase):
    pass

# ===== АНАЛИЗ ДОГОВОРОВ =====

class AnalyzeRequest(BaseModel):
    analysis_type: Literal["summary", "legal_check"]

class AnalyzeResponse(BaseModel):
    success: bool
    analysis_type: Optional[str] = None
    result: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None
    queued: Optional[bool] = False
    message: Optional[str] = None

# ===== ЭКСПОРТ =====

class ExportRequest(BaseModel):
    content: str
    filename: str = "Анализ_договора"
    content_type: str = "markdown"  # 'markdown' или 'html'

# ===== ПРОМПТЫ =====

class PromptsResponse(BaseModel):
    success: bool
    prompts: dict

class PromptSaveRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check"]
    content: str

class PromptResetRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check"]

# ===== НАСТРОЙКИ LLM =====

class LLMConfigResponse(BaseModel):
    success: bool
    config: dict

class LLMConfigUpdate(BaseModel):
    llm_type: Optional[Literal["deepseek", "lmstudio"]] = None
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    lmstudio_base_url: Optional[str] = None
    lmstudio_model: Optional[str] = None

# ===== НАСТРОЙКИ СИСТЕМЫ =====

class SettingsResponse(BaseModel):
    success: bool
    settings: dict

class SettingsUpdate(BaseModel):
    max_file_size_mb: Optional[int] = None
    max_queue_size: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None

# ===== СТАТИСТИКА ТОКЕНОВ =====

class TokensStatsResponse(BaseModel):
    success: bool
    stats: dict

# ===== ЛОГИ =====

class LogsResponse(BaseModel):
    success: bool
    logs: list

# ===== ОБЩИЕ =====

class SuccessResponse(BaseModel):
    success: bool
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
