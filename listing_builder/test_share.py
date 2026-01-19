#!/usr/bin/env python3
import gradio as gr
import sys

print(f'Gradio version: {gr.__version__}', flush=True)
print('Python:', sys.version, flush=True)

demo = gr.Interface(
    fn=lambda x: f'Echo: {x}',
    inputs='text',
    outputs='text',
    title='Listing Builder Pro - Test'
)

print('Launching with share=True...', flush=True)
print('Wait for public URL...', flush=True)
sys.stdout.flush()

demo.launch(share=True, server_name='0.0.0.0', server_port=7860)
