"""
Transcription Module
Video/Audio → Text pipeline for interview answer processing.

Priority chain:
  1. Gemini 2.5 Flash  — multimodal inline (< 20 MB) or File API (>= 20 MB)
  2. OpenAI Whisper API — whisper-1 model via REST API (no GPU needed)
  3. Browser Web Speech API draft — passed in as fallback_text

The highest-quality transcript is stored in the DB.
The source label is also persisted so evaluations can weight accordingly.
"""

import os
import logging
import tempfile
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ── Source label constants (stored in DB) ──────────────────────────────────────
SOURCE_GEMINI  = "gemini_multimodal"   # Server-side Gemini video understanding
SOURCE_WHISPER = "openai_whisper"      # Server-side Whisper API
SOURCE_BROWSER = "browser_stt"        # Browser Web Speech API (client-side)
SOURCE_MANUAL  = "manual_text"        # Candidate typed the answer manually
SOURCE_EMPTY   = "empty"             # No transcript obtained

# Gemini inline limit — use File API above this
_GEMINI_INLINE_LIMIT = 20 * 1024 * 1024  # 20 MB


class Transcriber:
    """
    Multi-provider video/audio → text transcription with graceful fallback.

    Usage:
        transcriber = Transcriber()
        text, source = transcriber.transcribe(video_bytes, fallback_text=browser_draft)
    """

    def __init__(self):
        self._gemini_key = os.getenv("GEMINI_API_KEY")
        self._openai_key = os.getenv("OPENAI_API_KEY")

        providers = []
        if self._gemini_key:
            providers.append("Gemini")
        if self._openai_key:
            providers.append("Whisper")
        providers.append("Browser-STT-fallback")
        logger.info(f"Transcriber initialised — provider chain: {' → '.join(providers)}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def transcribe(
        self,
        video_bytes: bytes,
        fallback_text: str = "",
    ) -> Tuple[str, str]:
        """
        Transcribe raw video bytes to text.

        Args:
            video_bytes:   Raw .webm bytes captured by MediaRecorder in the browser.
            fallback_text: Browser Web Speech API live draft (used if all server
                           providers fail, or if no video is provided).

        Returns:
            (transcript_text, source_label)
        """
        # No video — decide based on fallback text
        if not video_bytes:
            return self._resolve_fallback(fallback_text)

        # 1. Gemini multimodal (best quality, understands context)
        if self._gemini_key:
            text = self._gemini_transcribe(video_bytes)
            if text:
                logger.info(f"[Transcriber] Gemini succeeded — {len(text)} chars")
                return text, SOURCE_GEMINI

        # 2. OpenAI Whisper API (robust ASR, language-agnostic)
        if self._openai_key:
            text = self._whisper_transcribe(video_bytes)
            if text:
                logger.info(f"[Transcriber] Whisper succeeded — {len(text)} chars")
                return text, SOURCE_WHISPER

        # 3. Browser draft as last resort
        logger.warning("[Transcriber] All server providers failed — using browser draft")
        return self._resolve_fallback(fallback_text)

    # ── Gemini Multimodal ──────────────────────────────────────────────────────

    def _gemini_transcribe(self, video_bytes: bytes) -> Optional[str]:
        """
        Send video to Gemini 2.5 Flash for speech extraction.

        - Files < 20 MB: inline bytes (no temp file, fastest path)
        - Files >= 20 MB: Gemini File API upload (handles up to 2 GB)
        """
        try:
            from google import genai
            from google.genai import types  # noqa: F401

            client = genai.Client(api_key=self._gemini_key)

            _PROMPT = (
                "You are transcribing a job interview audio response. "
                "Extract and output ONLY the spoken words from this video, "
                "preserving natural sentence flow with correct punctuation. "
                "Do NOT add speaker labels, timestamps, filler annotations, "
                "or any commentary. "
                "If the video contains no audible speech, output exactly: "
                "[No speech detected]"
            )

            if len(video_bytes) < _GEMINI_INLINE_LIMIT:
                # ── Inline path (fast, no disk I/O) ──────────────────────────
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(
                            data=video_bytes,
                            mime_type="video/webm",
                        ),
                        _PROMPT,
                    ],
                )
            else:
                # ── File API path (large videos) ──────────────────────────────
                size_mb = len(video_bytes) / 1024 / 1024
                logger.info(f"[Transcriber] Video is {size_mb:.1f} MB — using Gemini File API")

                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        suffix=".webm", delete=False
                    ) as tmp:
                        tmp.write(video_bytes)
                        tmp_path = tmp.name

                    file_ref = client.files.upload(
                        file=tmp_path,
                        config=types.UploadFileConfig(mime_type="video/webm"),
                    )
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[file_ref, _PROMPT],
                    )
                finally:
                    if tmp_path:
                        try:
                            os.unlink(tmp_path)
                        except OSError:
                            pass

            text = (response.text or "").strip()
            return None if (not text or text == "[No speech detected]") else text

        except ImportError:
            logger.warning(
                "[Transcriber] google-genai not installed — skipping Gemini"
            )
            return None
        except Exception as exc:
            logger.error(f"[Transcriber] Gemini error: {exc}")
            return None

    # ── OpenAI Whisper API ─────────────────────────────────────────────────────

    def _whisper_transcribe(self, video_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio via OpenAI Whisper API (whisper-1).

        No GPU required — this calls the hosted OpenAI endpoint.
        The .webm container is accepted directly by the API.
        """
        tmp_path = None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._openai_key)

            # Whisper endpoint requires a real file handle with a name
            with tempfile.NamedTemporaryFile(
                suffix=".webm", delete=False
            ) as tmp:
                tmp.write(video_bytes)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="en",
                )

            # Whisper returns a plain string when response_format="text"
            text = result.strip() if isinstance(result, str) else str(result).strip()
            return text if text else None

        except ImportError:
            logger.warning(
                "[Transcriber] openai package not installed — skipping Whisper"
            )
            return None
        except Exception as exc:
            logger.error(f"[Transcriber] Whisper error: {exc}")
            return None
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve_fallback(fallback_text: str) -> Tuple[str, str]:
        """Return browser draft or empty, with appropriate source label."""
        _PLACEHOLDER = "[Video response recorded]"
        text = (fallback_text or "").strip()
        if text and text != _PLACEHOLDER:
            return text, SOURCE_BROWSER
        return text, SOURCE_EMPTY
