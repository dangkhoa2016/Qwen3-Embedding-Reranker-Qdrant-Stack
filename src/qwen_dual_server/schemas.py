from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    input_type: Literal["query", "document"] = "query"
    instruction: str | None = None

    @model_validator(mode="after")
    def non_empty_input(self):
        items = [self.input] if isinstance(self.input, str) else self.input
        if not items or any(not isinstance(item, str) or not item.strip() for item in items):
            raise ValueError("input must contain non-empty strings")
        return self


class RerankRequest(BaseModel):
    query: str = Field(min_length=1)
    documents: list[str] = Field(min_length=1)
    instruction: str | None = None
    return_documents: bool = False

    @field_validator("documents")
    @classmethod
    def documents_non_empty(cls, value: list[str]):
        if any(not item.strip() for item in value):
            raise ValueError("documents must contain non-empty strings")
        return value
