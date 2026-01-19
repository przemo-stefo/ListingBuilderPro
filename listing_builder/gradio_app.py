#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/gradio_app.py
# Purpose: Gradio web GUI for Amazon Listing Builder
# NOT for: Command-line interface (use cli.py for that)

"""
Gradio Web GUI
Interactive web interface for Amazon Listing Builder with file uploads.
"""

import gradio as gr
import os
import tempfile
from listing_optimizer import optimize_listing
from output import save_listing_to_file


def optimize_listing_gui(
    # Required inputs
    datadive_file,
    brand_name,
    product_line,
    mode,
    # Optional inputs
    cerebro_file=None,
    magnet_file=None,
    additional_files=None,
    min_volume=0,
    merge_strategy="union"
):
    """
    GUI wrapper for listing optimizer.

    WHY: Handles file uploads and returns results for display
    WHY: Saves output file for download
    """
    try:
        # WHY: Validate required inputs
        if not datadive_file:
            return "❌ ERROR: Please upload a Data Dive CSV file", None
        if not brand_name or not product_line:
            return "❌ ERROR: Please enter Brand Name and Product Line", None

        # WHY: Get file paths from uploaded files
        datadive_path = datadive_file.name
        cerebro_path = cerebro_file.name if cerebro_file else None
        magnet_path = magnet_file.name if magnet_file else None

        # WHY: Handle multiple additional files
        additional_paths = []
        if additional_files:
            additional_paths = [f.name for f in additional_files]

        # WHY: Build output for display
        output_lines = []
        output_lines.append("="*60)
        output_lines.append("🚀 AMAZON LISTING OPTIMIZER")
        output_lines.append("="*60)
        output_lines.append(f"\n📋 Configuration:")
        output_lines.append(f"   Brand: {brand_name}")
        output_lines.append(f"   Product: {product_line}")
        output_lines.append(f"   Mode: {mode.upper()}")

        if cerebro_path:
            output_lines.append(f"   ✓ Cerebro CSV provided")
        if magnet_path:
            output_lines.append(f"   ✓ Magnet CSV provided")
        if additional_paths:
            output_lines.append(f"   ✓ {len(additional_paths)} additional Data Dive files")
        if min_volume > 0:
            output_lines.append(f"   ✓ Min volume filter: {min_volume}/month")

        output_lines.append("\n" + "="*60)
        output_lines.append("Processing...")
        output_lines.append("="*60 + "\n")

        # WHY: Run optimization
        result = optimize_listing(
            csv_path=datadive_path,
            brand=brand_name,
            product_line=product_line,
            mode=mode.lower(),
            cerebro_csv=cerebro_path,
            magnet_csv=magnet_path,
            additional_datadive_csvs=additional_paths if additional_paths else None,
            min_search_volume=int(min_volume),
            merge_strategy=merge_strategy.lower()
        )

        # WHY: Generate summary output
        output_lines.append("\n" + "="*60)
        output_lines.append("✅ OPTIMIZATION COMPLETE!")
        output_lines.append("="*60 + "\n")

        listing = result['listing']
        stats = result['stats']
        validation = result['validation']

        # WHY: Show results summary
        output_lines.append(f"📊 Results:")
        output_lines.append(f"   Coverage: {stats['coverage_pct']:.1f}% ({stats['mode']})")
        output_lines.append(f"   EXACT matches: {stats['exact_matches']}")
        output_lines.append(f"   Title: {stats['title_stats']['length']} chars")
        output_lines.append(f"   Backend: {stats['backend_stats']['byte_size']}/250 bytes")
        output_lines.append(f"   Validation: {'✅ ALL PASS' if validation['all_valid'] else '⚠️ ISSUES DETECTED'}\n")

        output_lines.append("="*60)
        output_lines.append("OPTIMIZED LISTING")
        output_lines.append("="*60 + "\n")

        output_lines.append("📝 TITLE:")
        output_lines.append("-"*60)
        output_lines.append(listing['title'])
        output_lines.append("\n")

        output_lines.append("🔹 BULLET POINTS:")
        output_lines.append("-"*60)
        for i, bullet in enumerate(listing['bullets'], 1):
            output_lines.append(f"{i}. {bullet}\n")

        output_lines.append("📄 DESCRIPTION:")
        output_lines.append("-"*60)
        output_lines.append(listing['description'])
        output_lines.append("\n")

        output_lines.append("🔧 BACKEND SEARCH TERMS:")
        output_lines.append("-"*60)
        output_lines.append(listing['backend'])
        output_lines.append("\n")

        output_lines.append("="*60)
        output_lines.append("STATISTICS")
        output_lines.append("="*60 + "\n")

        output_lines.append(f"Coverage: {stats['coverage_pct']:.1f}%")
        output_lines.append(f"Mode: {stats['mode']}")
        output_lines.append(f"EXACT matches in title: {stats['exact_matches']}")
        output_lines.append(f"Title: {stats['title_stats']['length']}/200 chars ({stats['title_stats']['utilization']:.1f}%)")
        output_lines.append(f"Bullets: {stats['bullet_stats']['bullet_count']} bullets")
        output_lines.append(f"Backend: {stats['backend_stats']['byte_size']}/250 bytes ({stats['backend_stats']['utilization']:.1f}%)")

        section_cov = stats['section_coverage']
        output_lines.append(f"\nSection Coverage:")
        output_lines.append(f"  Title: {section_cov['title_coverage']:.1f}%")
        output_lines.append(f"  Bullets: {section_cov['bullets_coverage']:.1f}%")
        output_lines.append(f"  Backend: {section_cov['backend_coverage']:.1f}%")

        # WHY: Save to file for download
        output_filename = f"optimized_listing_{brand_name.replace(' ', '_')}.txt"
        save_listing_to_file(result, output_filename)

        # WHY: Return output text and file path for download
        return "\n".join(output_lines), output_filename

    except Exception as e:
        return f"❌ ERROR: {str(e)}\n\nPlease check your inputs and try again.", None


# WHY: Create Gradio interface
with gr.Blocks(title="Amazon Listing Builder v2.0", theme=gr.themes.Soft()) as app:

    gr.Markdown("""
    # 🚀 Amazon Listing Builder v2.0

    **Generate optimized Amazon listings with competitor analysis, keyword variations, and more!**

    Upload your CSV files and configure your listing below.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📁 Required Inputs")

            datadive_input = gr.File(
                label="Data Dive CSV (Required)",
                file_types=[".csv"],
                type="filepath"
            )

            brand_input = gr.Textbox(
                label="Brand Name",
                placeholder="e.g., HAG EXPRESS",
                info="Your brand name (as it should appear in title)"
            )

            product_input = gr.Textbox(
                label="Product Line",
                placeholder="e.g., Bamboo Cutting Board Set",
                info="Your product line description"
            )

            mode_input = gr.Dropdown(
                label="Optimization Mode",
                choices=["Aggressive", "Standard"],
                value="Aggressive",
                info="Aggressive = 96-98% coverage, Standard = 82-85%"
            )

            gr.Markdown("---")
            gr.Markdown("### ✨ Optional Enhancements")

            cerebro_input = gr.File(
                label="Cerebro CSV (Optional)",
                file_types=[".csv"],
                type="filepath",
                info="Helium 10 Cerebro export for competitor gap analysis"
            )

            magnet_input = gr.File(
                label="Magnet CSV (Optional)",
                file_types=[".csv"],
                type="filepath",
                info="Helium 10 Magnet export for keyword variations"
            )

            additional_input = gr.Files(
                label="Additional Data Dive CSVs (Optional)",
                file_types=[".csv"],
                type="filepath",
                info="Multiple Data Dive files to merge"
            )

            with gr.Row():
                min_volume_input = gr.Number(
                    label="Min Search Volume",
                    value=0,
                    minimum=0,
                    step=10,
                    info="Filter keywords below this volume (0 = no filter)"
                )

                merge_strategy_input = gr.Dropdown(
                    label="Merge Strategy",
                    choices=["Union", "Intersection"],
                    value="Union",
                    info="For multiple Data Dive files"
                )

            optimize_btn = gr.Button("🚀 Generate Optimized Listing", variant="primary", size="lg")

        with gr.Column(scale=2):
            gr.Markdown("### 📊 Results")

            output_text = gr.Textbox(
                label="Optimized Listing Output",
                lines=25,
                max_lines=50,
                show_copy_button=True,
                info="Your optimized listing will appear here"
            )

            download_file = gr.File(
                label="Download Listing File",
                interactive=False
            )

            gr.Markdown("""
            ---
            ### 💡 Quick Tips
            - **Data Dive CSV**: Export from Helium 10 Data Dive (Listing Builder format)
            - **Cerebro CSV**: Find keywords competitors rank for that you don't
            - **Magnet CSV**: Expand with related terms and synonyms
            - **Min Volume**: Focus on high-traffic keywords (try 100+)

            ### 📚 Documentation
            See `PRODUCTION_README.md` for detailed instructions on exporting CSVs from Helium 10.
            """)

    # WHY: Connect button to function
    optimize_btn.click(
        fn=optimize_listing_gui,
        inputs=[
            datadive_input,
            brand_input,
            product_input,
            mode_input,
            cerebro_input,
            magnet_input,
            additional_input,
            min_volume_input,
            merge_strategy_input
        ],
        outputs=[output_text, download_file]
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Amazon Listing Builder v2.0 - Web GUI")
    print("="*60)
    print("\nStarting web interface...")
    print("GUI will open in your browser automatically.\n")

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        inbrowser=False
    )
