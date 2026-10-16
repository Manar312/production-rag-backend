import httpx
import logging

from src.core.config import get_settings
from src.services.embedding_service import get_embedding_service
from src.services.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


class QueryService:
    async def answer(
        self,
        project_id: str,
        question: str,
        top_k: int = 5,
    ) -> dict:
        settings = get_settings()
        embedding_service = get_embedding_service()
        vector_store = VectorStoreService()

        try:
            query_vector = embedding_service.embed_query(question)
            matches = vector_store.search(
                query_vector=query_vector,
                project_id=project_id,
                limit=top_k,
            )
        finally:
            vector_store.close()

        sources = [
            {
                "asset_id": str(item.get("asset_id", "")),
                "source": str(item.get("source", "Unknown source")),
                "page_number": item.get("page_number"),
                "sheet_name": item.get("sheet_name"),
                "slide_number": item.get("slide_number"),
                "chunk_index": int(item.get("chunk_index", 0)),
                "score": float(item.get("score", 0.0)),
                "text": str(item.get("text", "")),
            }
            for item in matches
            if item.get("text")
        ]

        if not sources:
            return {
                "project_id": project_id,
                "question": question,
                "answer": (
                    "لم أجد مقاطع مفهرسة لهذا السؤال داخل مستندات هذا المشروع. "
                    "تأكدي من اكتمال معالجة الملف ثم جرّبي مرة أخرى."
                ),
                "generation_used": False,
                "sources": [],
            }

        generation_used = False
        answer = (
            "لم يتم إعداد مزوّد توليد الإجابات بعد. "
            "هذه المقاطع المسترجعة ذات الصلة، وليست إجابة مولّدة:\n\n"
            + "\n\n".join(
                f"[{index}] {source['text']}"
                for index, source in enumerate(sources, start=1)
            )
        )

        if (
            settings.LLM_API_KEY.strip()
            and settings.LLM_BASE_URL.strip()
            and settings.LLM_MODEL.strip()
        ):
            base_url = settings.LLM_BASE_URL.rstrip("/")
            endpoint = (
                base_url
                if base_url.endswith("/chat/completions")
                else f"{base_url}/chat/completions"
            )

            context = "\n\n".join(
                f"[{index}] source={source['source']}; "
                f"page={source['page_number']}; "
                f"sheet={source['sheet_name']}; "
                f"slide={source['slide_number']}\n"
                f"{source['text']}"
                for index, source in enumerate(sources, start=1)
            )

            system_prompt = (
                "Answer the user's question using only the supplied "
                "document excerpts. If the excerpts do not support an "
                "answer, say so. Do not invent facts or sources. "
                "Answer in the same language as the user's question. "
                "Cite supporting excerpt numbers like [1] and [2]."
            )

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {settings.LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.LLM_MODEL,
                        "temperature": 0,
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt,
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Question:\n{question}\n\n"
                                    f"Document excerpts:\n{context}"
                                ),
                            },
                        ],
                    },
                )

                if response.is_error:
                    logger.error(
                        "LLM provider returned HTTP status %s.",
                        response.status_code,
                    )

                response.raise_for_status()

                try:
                    data = response.json()
                    choices = data["choices"]
                    first_choice = choices[0]
                    message = first_choice["message"]
                    answer = message["content"]
                except (
                    ValueError,
                    KeyError,
                    IndexError,
                    TypeError,
                ) as exc:
                    raise RuntimeError(
                        "LLM provider returned an invalid response."
                    ) from exc

            if not isinstance(answer, str) or not answer.strip():
                raise RuntimeError("LLM returned an empty answer.")

            answer = answer.strip()
            generation_used = True

        return {
            "project_id": project_id,
            "question": question,
            "answer": answer,
            "generation_used": generation_used,
            "sources": sources,
        }