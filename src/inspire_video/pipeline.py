"""Pipeline orchestration entry point — implementation TODO.

Suggested stages:
1. probe_source
2. extract_audio
3. transcribe
4. select_segments (LLM structured output)
5. translate_and_write_copy
6. cut_clip
7. build_manifest
8. render_remotion
9. validate_output

Keep provider adapters separate from orchestration so local and hosted models
can be swapped without changing the render pipeline.
"""
