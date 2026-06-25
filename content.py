"""
Servicio de generación de contenido usando la API de Claude (Anthropic).
Instalar: pip install anthropic
Configurar: export ANTHROPIC_API_KEY=sk-ant-...
"""
import asyncio
import os
import json
from typing import Optional


async def generate_content(transcript: str) -> dict:
    """
    Genera copies, hashtags y estructura de carrusel a partir de la transcripción.

    Devuelve:
    {
        "copies": ["copy corto", "copy largo", "copy con CTA"],
        "hashtags": ["#marketing", "#contenido", ...],
        "carousel_slides": [
            {"title": "...", "body": "..."},
            ...
        ],
        "cover_texts": ["texto portada 1", "texto portada 2"],
    }
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _call_claude, transcript)


def _call_claude(transcript: str) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return _stub_content(transcript)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Analiza esta transcripción de video y genera contenido para redes sociales.

TRANSCRIPCIÓN:
{transcript}

Responde ÚNICAMENTE con un JSON válido (sin backticks, sin texto extra) con esta estructura:
{{
  "copies": [
    "Copy corto (máx 150 caracteres, con emoji, ideal para historia)",
    "Copy medio (150-300 caracteres, con hook y CTA)",
    "Copy largo (300-500 caracteres, storytelling con llamada a la acción)"
  ],
  "hashtags": ["#hashtag1", "#hashtag2", ...],
  "carousel_slides": [
    {{"title": "Título impactante", "body": "Desarrollo en 1-2 oraciones"}},
    ...
  ],
  "cover_texts": [
    "Texto llamativo para portada 1 (máx 8 palabras)",
    "Texto alternativo para portada 2"
  ]
}}

Reglas:
- copies: 3 versiones adaptadas a diferentes formatos
- hashtags: exactamente 25, mezcla de populares y de nicho, en español e inglés
- carousel_slides: 5-7 slides, cada uno con un punto clave del video
- cover_texts: 2 opciones de texto corto y poderoso para la miniatura
- Todo en español (salvo los hashtags en inglés)
"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()
        # Limpiar posibles backticks si el modelo los incluyó
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)

    except Exception as e:
        print(f"[Claude API error] {e}")
        return _stub_content(transcript)


def _stub_content(transcript: str) -> dict:
    """Contenido de ejemplo cuando la API no está disponible."""
    return {
        "copies": [
            "🚀 ¿Quieres hacer crecer tu negocio en redes? Estas 3 claves lo cambian todo. ¡Guarda este video!",
            "El 90% de los creadores falla por ignorar esto 👇\n\nConsistencia · Valor real · Comunidad genuina\n\nSi aplicas estas 3 claves, los resultados llegan. ¿Cuál te cuesta más? 👇",
            "Llevo años estudiando cómo los negocios crecen en redes sociales y hay un patrón claro.\n\nNo es el algoritmo. No es el presupuesto.\n\nSon 3 principios que los que triunfan aplican sin excepción:\n\n✅ Consistencia (publicar aunque no tengas ganas)\n✅ Valor real (que tu audiencia aprenda algo)\n✅ Comunidad genuina (responder, conectar, estar presente)\n\nEmpieza hoy con uno solo. La semana que viene añade otro. En 90 días los resultados hablan. 👇 Cuéntame en comentarios: ¿en cuál estás fallando?",
        ],
        "hashtags": [
            "#marketing", "#redessociales", "#contenidodigital", "#emprendimiento",
            "#negociosonline", "#creadores", "#estrategiadigital", "#crecimiento",
            "#comunidad", "#consistencia", "#socialmedia", "#contentcreator",
            "#marketingdigital", "#emprender", "#videocontent", "#reels",
            "#instagramtips", "#tiktokmarketing", "#contentmarketing", "#branding",
            "#entrepreneur", "#growthhacking", "#digitalmarketing", "#business",
            "#creatoreconomy",
        ],
        "carousel_slides": [
            {"title": "3 claves para crecer en redes", "body": "Lo que separa a los que crecen de los que se estancan."},
            {"title": "1. Consistencia", "body": "Publica aunque no tengas ganas. El algoritmo premia la regularidad."},
            {"title": "2. Valor real", "body": "Cada pieza de contenido debe resolver un problema o enseñar algo concreto."},
            {"title": "3. Comunidad genuina", "body": "Responde comentarios. Conecta. Las personas siguen a personas, no a marcas."},
            {"title": "El error más común", "body": "Buscar el viral antes de tener una base sólida de seguidores fieles."},
            {"title": "Empieza hoy", "body": "Un post. Una historia. Una respuesta. La consistencia se construye día a día."},
        ],
        "cover_texts": [
            "3 claves que nadie te cuenta",
            "Así crecí mi negocio en redes",
        ],
    }
