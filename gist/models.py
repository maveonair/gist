import markdown2
from sqlalchemy import Column, DateTime, Integer, String, Text

from .database import Base


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, unique=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def render(self, full=True):
        if full:
            return markdown2.markdown(self.content, extras=["fenced-code-blocks"])

        truncated = self.content[0:250]
        if truncated.startswith("```") and not truncated.endswith("```"):
            truncated = f"{truncated}\n```"

        return markdown2.markdown(truncated, extras=["fenced-code-blocks"])
