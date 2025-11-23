"""Template service for managing conversation templates."""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.analytics import ConversationTemplate
from app.core.logging import get_logger

logger = get_logger(__name__)


class TemplateService:
    """Service for managing conversation templates."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize template service."""
        self.db = db

    async def create_template(
        self,
        name: str,
        description: Optional[str],
        system_prompt: Optional[str],
        model_config: Optional[Dict[str, Any]],
        user_id: Optional[str] = None,
        is_public: bool = False,
    ) -> ConversationTemplate:
        """Create a new conversation template."""
        template = ConversationTemplate(
            user_id=user_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            model_config=model_config,
            is_public=is_public,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(f"Created template: {name}")
        return template

    async def get_template(
        self,
        template_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[ConversationTemplate]:
        """Get a template by ID."""
        query = select(ConversationTemplate).where(
            ConversationTemplate.id == template_id
        )

        # If user_id provided, check ownership or public status
        if user_id:
            query = query.where(
                and_(
                    ConversationTemplate.id == template_id,
                    (ConversationTemplate.user_id == user_id) |
                    (ConversationTemplate.is_public == True)
                )
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        user_id: Optional[str] = None,
        public_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ConversationTemplate]:
        """List templates."""
        query = select(ConversationTemplate)

        if public_only:
            query = query.where(ConversationTemplate.is_public == True)
        elif user_id:
            query = query.where(
                (ConversationTemplate.user_id == user_id) |
                (ConversationTemplate.is_public == True)
            )

        query = query.order_by(ConversationTemplate.usage_count.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_template(
        self,
        template_id: str,
        user_id: str,
        **updates: Any,
    ) -> Optional[ConversationTemplate]:
        """Update a template."""
        template = await self.get_template(template_id)

        if not template or template.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)

        await self.db.commit()
        await self.db.refresh(template)

        logger.info(f"Updated template: {template_id}")
        return template

    async def delete_template(
        self,
        template_id: str,
        user_id: str,
    ) -> bool:
        """Delete a template."""
        template = await self.get_template(template_id)

        if not template or template.user_id != user_id:
            return False

        await self.db.delete(template)
        await self.db.commit()

        logger.info(f"Deleted template: {template_id}")
        return True

    async def increment_usage(self, template_id: str) -> None:
        """Increment template usage count."""
        template = await self.get_template(template_id)

        if template:
            template.usage_count += 1
            await self.db.commit()

    async def get_popular_templates(
        self,
        limit: int = 10,
    ) -> List[ConversationTemplate]:
        """Get most popular public templates."""
        result = await self.db.execute(
            select(ConversationTemplate)
            .where(ConversationTemplate.is_public == True)
            .order_by(ConversationTemplate.usage_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# Pre-defined system templates
SYSTEM_TEMPLATES = [
    {
        "name": "Code Assistant",
        "description": "Expert programmer who helps with coding questions",
        "system_prompt": "You are an expert programmer with deep knowledge of multiple programming languages. You provide clear, well-commented code examples and explain complex concepts simply. Always consider best practices and security.",
        "model_config": {"temperature": 0.3, "max_tokens": 2000},
    },
    {
        "name": "Creative Writer",
        "description": "Creative writing assistant for stories and content",
        "system_prompt": "You are a creative writing assistant with expertise in storytelling, character development, and engaging narratives. You help users craft compelling stories, improve their writing, and explore creative ideas.",
        "model_config": {"temperature": 0.9, "max_tokens": 3000},
    },
    {
        "name": "Data Analyst",
        "description": "Data analysis and visualization expert",
        "system_prompt": "You are a data analyst expert who helps users understand data, create visualizations, and derive insights. You explain statistical concepts clearly and provide actionable recommendations.",
        "model_config": {"temperature": 0.5, "max_tokens": 2000},
    },
    {
        "name": "Business Advisor",
        "description": "Strategic business and startup advisor",
        "system_prompt": "You are a business strategy consultant with expertise in startups, product development, and market analysis. You provide practical, actionable business advice and help think through strategic decisions.",
        "model_config": {"temperature": 0.7, "max_tokens": 2000},
    },
    {
        "name": "Academic Tutor",
        "description": "Patient tutor for various academic subjects",
        "system_prompt": "You are a patient and knowledgeable tutor who helps students understand complex academic concepts. You break down difficult topics into manageable pieces and use examples to illustrate key points.",
        "model_config": {"temperature": 0.6, "max_tokens": 2500},
    },
    {
        "name": "Technical Writer",
        "description": "Documentation and technical writing specialist",
        "system_prompt": "You are a technical writer who creates clear, concise documentation. You help structure information logically, write user-friendly guides, and ensure technical content is accessible to the target audience.",
        "model_config": {"temperature": 0.4, "max_tokens": 2000},
    },
]
