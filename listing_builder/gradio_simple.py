#!/usr/bin/env python3
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/gradio_simple.py
# Purpose: Simple Gradio demo for Listing Builder - compatible with latest Gradio
# NOT for: Full production features

"""
Simple Listing Builder Demo
Clean, minimal interface for demo purposes.
"""

import gradio as gr
import pandas as pd
import os

# Try to import AI assistant, fallback to simple response
try:
    from ai_assistant import get_answer
    HAS_AI = True
except:
    HAS_AI = False

def analyze_csv(file):
    """Parse uploaded CSV and return analysis."""
    if file is None:
        return "❌ Proszę załadować plik CSV"

    try:
        df = pd.read_csv(file.name)

        # Detect file type and extract relevant columns
        cols = df.columns.tolist()

        report = "# 📊 Analiza CSV\n\n"
        report += f"**Liczba wierszy:** {len(df)}\n"
        report += f"**Kolumny:** {', '.join(cols[:10])}\n\n"

        # Try to find keyword column
        keyword_col = None
        for col in cols:
            if 'keyword' in col.lower() or 'phrase' in col.lower():
                keyword_col = col
                break

        if keyword_col:
            report += f"## Top 10 Keywords\n\n"
            top_kw = df[keyword_col].head(10).tolist()
            for i, kw in enumerate(top_kw, 1):
                report += f"{i}. {kw}\n"

        # Try to find volume column
        volume_col = None
        for col in cols:
            if 'volume' in col.lower() or 'search' in col.lower():
                volume_col = col
                break

        if volume_col:
            try:
                total_vol = df[volume_col].sum()
                avg_vol = df[volume_col].mean()
                report += f"\n## Volume Stats\n"
                report += f"- **Total Search Volume:** {total_vol:,.0f}\n"
                report += f"- **Average Volume:** {avg_vol:,.0f}\n"
            except:
                pass

        return report

    except Exception as e:
        return f"❌ Błąd parsowania: {str(e)}"


def generate_listing(keywords_text, brand_name, product_type):
    """Generate listing based on keywords."""
    if not keywords_text or not brand_name:
        return "❌ Wprowadź słowa kluczowe i nazwę marki"

    keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()][:20]

    if not keywords:
        return "❌ Brak słów kluczowych"

    # Generate title (max 200 chars, front-loaded keywords)
    title_keywords = keywords[:5]
    title = f"{brand_name} {product_type} - " + ", ".join(title_keywords)
    if len(title) > 200:
        title = title[:197] + "..."

    # Generate bullets
    bullets = []
    bullet_templates = [
        "✅ PREMIUM QUALITY - {kw} designed for maximum performance and durability",
        "✅ EASY TO USE - Perfect {kw} for beginners and professionals alike",
        "✅ VERSATILE - Works great as {kw} for multiple applications",
        "✅ VALUE PACK - Get the best {kw} at an unbeatable price",
        "✅ SATISFACTION GUARANTEED - Our {kw} comes with full warranty"
    ]

    for i, template in enumerate(bullet_templates):
        kw = keywords[i] if i < len(keywords) else keywords[0]
        bullets.append(template.format(kw=kw))

    # Generate backend keywords (250 bytes max)
    backend = ", ".join(keywords[:15])
    if len(backend.encode('utf-8')) > 250:
        backend = backend[:247] + "..."

    bullets_text = "\n".join([f"• {b}" for b in bullets])

    result = f"""# 📝 Wygenerowany Listing

## Title (max 200 znaków)
{title}

## Bullet Points
{bullets_text}

## Backend Keywords (max 250 bytes)
{backend}

---
**Keywords użyte:** {len(keywords)}
**Marka:** {brand_name}
**Typ produktu:** {product_type}
"""

    return result


def chat_with_ai(message, history):
    """Simple chat function."""
    if not message:
        return history

    if HAS_AI:
        try:
            response = get_answer(message)
        except:
            response = "AI Assistant jest niedostępny. Sprawdź konfigurację API."
    else:
        response = f"""Otrzymałem pytanie: "{message}"

AI Assistant wymaga konfiguracji klucza API Anthropic.
Ustaw zmienną środowiskową ANTHROPIC_API_KEY.

W międzyczasie mogę pomóc z:
- Analizą CSV (zakładka "Analiza CSV")
- Generowaniem listingów (zakładka "Generator")
"""

    history = history + [[message, response]]
    return history


# Build interface
with gr.Blocks(
    title="Amazon Listing Builder Pro",
    theme=gr.themes.Soft()
) as app:

    gr.Markdown("""
    # 🚀 Amazon Listing Builder Pro
    ### AI-powered listing optimization tool
    """)

    with gr.Tabs():
        # Tab 1: CSV Analysis
        with gr.TabItem("📊 Analiza CSV"):
            gr.Markdown("Upload plik CSV z Helium 10, Data Dive lub Black Box")

            with gr.Row():
                csv_input = gr.File(
                    label="Upload CSV",
                    file_types=[".csv"]
                )

            analyze_btn = gr.Button("🔍 Analizuj", variant="primary")
            analysis_output = gr.Markdown(label="Wyniki analizy")

            analyze_btn.click(
                fn=analyze_csv,
                inputs=[csv_input],
                outputs=[analysis_output]
            )

        # Tab 2: Listing Generator
        with gr.TabItem("✍️ Generator Listingu"):
            gr.Markdown("Wygeneruj zoptymalizowany listing Amazon")

            with gr.Row():
                with gr.Column():
                    brand_input = gr.Textbox(
                        label="Nazwa Marki",
                        placeholder="np. MyBrand"
                    )
                    product_input = gr.Textbox(
                        label="Typ Produktu",
                        placeholder="np. Yoga Mat"
                    )
                    keywords_input = gr.Textbox(
                        label="Słowa Kluczowe (jedno na linię)",
                        placeholder="yoga mat\nexercise mat\nfitness mat",
                        lines=10
                    )

                with gr.Column():
                    generate_btn = gr.Button("🚀 Generuj Listing", variant="primary")
                    listing_output = gr.Markdown(label="Wygenerowany Listing")

            generate_btn.click(
                fn=generate_listing,
                inputs=[keywords_input, brand_input, product_input],
                outputs=[listing_output]
            )

        # Tab 3: AI Assistant
        with gr.TabItem("🤖 AI Asystent"):
            gr.Markdown("Zapytaj o strategię Amazon, optymalizację listingów, PPC i więcej")

            chatbot = gr.Chatbot(
                value=[[None, "👋 Cześć! Jestem AI Asystentem Amazon. Zapytaj mnie o:\n\n• Strategię listingów\n• Optymalizację słów kluczowych\n• PPC i reklamy\n• Analizę konkurencji\n\nW czym mogę pomóc?"]],
                height=400
            )

            with gr.Row():
                msg_input = gr.Textbox(
                    label="Twoje pytanie",
                    placeholder="Wpisz pytanie o Amazon...",
                    scale=4
                )
                send_btn = gr.Button("Wyślij", variant="primary", scale=1)

            send_btn.click(
                fn=chat_with_ai,
                inputs=[msg_input, chatbot],
                outputs=[chatbot]
            )
            msg_input.submit(
                fn=chat_with_ai,
                inputs=[msg_input, chatbot],
                outputs=[chatbot]
            )

    gr.Markdown("""
    ---
    **Listing Builder Pro** | Built with ❤️ for Amazon Sellers
    """)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Amazon Listing Builder Pro - Demo Mode")
    print("="*60)
    print("\nStarting Gradio interface with public share link...")

    app.launch(
        server_name="localhost",
        server_port=7860,
        share=False
    )
