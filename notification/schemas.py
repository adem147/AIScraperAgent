from pydantic import BaseModel, Field


class SMTPSettings(BaseModel):
    provider: str = Field(pattern="^(gmail|outlook|sendgrid)$")
    sender: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    recipient: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    username: str = Field(min_length=1, max_length=320)
    password: str = Field(default="", max_length=500)
    host: str = Field(default="", max_length=255)
    port: int = Field(default=465, ge=1, le=65535)
    use_ssl: bool = True