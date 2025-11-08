import os
from fastapi import APIRouter
from ..models.schemas import ChatRequest, ChatResponse
from ..rag.vector_store import search
from groq import Groq

router = APIRouter(prefix="/api", tags=["chat"])

_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

_SYSTEM = (
    "You are a helpful clinic assistant. Use the provided context faithfully. "
    "If the answer isn't in the context, say you don't know and suggest calling the clinic."
)

def _format_context(pairs: list[tuple[str,str]]) -> str:
    lines = []
    for txt, src in pairs:
        src = src or "clinic_info"
        lines.append(f"- ({src}) {txt}")
    return "\n".join(lines)

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    ctx_pairs = search(req.question, top_k=4)
    ctx = _format_context(ctx_pairs) if ctx_pairs else "No context found."

    prompt = (
        f"Context:\n{ctx}\n\n"
        f"User question: {req.question}\n\n"
        "Answer concisely and cite source names in parentheses inline."
    )

    completion = _groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    answer = completion.choices[0].message.content
    sources = list({s for _, s in ctx_pairs if s})
    return ChatResponse(answer=answer, sources=sources)
