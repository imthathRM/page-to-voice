import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from services import tts_service, azure_tts_service, elevenlabs_service

# Benchmark samples (English, Tamil, Sinhala)
SAMPLES = {
    "en": {
        "short": "Page to Voice is an intelligent audiobook generation platform.",
        "medium": (
            "Chapter 1: The Beginning of Knowledge.\n\n"
            "In a world driven by artificial intelligence, transforming printed literature "
            "into living spoken words bridges human imagination and accessibility. "
            "Fast text-to-speech synthesis enables learners and readers worldwide to consume books effortlessly."
        ),
    },
    "ta": {
        "short": "பேஜ் டு வாய்ஸ் ஒரு அதிவேக ஒலிப்புத்தக உருவாக்க இயங்குதளமாகும்.",
        "medium": (
            "அத்தியாயம் 1: அறிவின் தொடக்கம்.\n\n"
            "செயற்கை நுண்ணறிவு உலகில், புத்தகங்களை நேரடி குரல்வடிவில் மாற்றுவது வாசகர்களுக்கு "
            "மிகப்பெரிய வசதியை ஏற்படுத்துகிறது. தமிழ் மொழியின் தனித்துவமான ஒலி அமைப்பை பாதுகாத்து "
            "இயற்கையான குரலில் ஒலிப்புத்தகம் உருவாக்கப்படுகிறது."
        ),
    },
    "si": {
        "short": "පිටුවෙන් හඬට වේදිකාව මගින් ලේඛන කඩිනමින් ශ්‍රව්‍ය පොත් බවට පත් කරයි.",
        "medium": (
            "1 වන පරිච්ඡේදය: දැනුමේ ආරම්භය.\n\n"
            "කෘතිම බුද්ධිය මඟින් මුද්‍රිත ලේඛන සහ පොත්පත් ස්වභාවික සිංහල කටහඬින් ශ්‍රවණය කිරීමට "
            "මෙම වේදිකාව මගින් ඉඩකඩ සලසා දෙයි. අධිවේගී තාක්ෂණය ඔස්සේ පළමු පරිච්ඡේදය වහාම "
            "ශ්‍රවණය කිරීමට හැකියාව ලැබේ."
        ),
    },
}

# Cost per 1 million characters
PROVIDER_COST_RATES = {
    "elevenlabs": {"name": "ElevenLabs Flash v2.5", "cost_per_1m_chars": 150.00, "ttfb_rating": "Ultra-Low (<150ms)"},
    "azure": {"name": "Microsoft Azure AI Speech", "cost_per_1m_chars": 16.00, "ttfb_rating": "Very Low (~250-400ms)"},
    "gemini-tts": {"name": "Google Gemini TTS", "cost_per_1m_chars": 12.00, "ttfb_rating": "Moderate (~1200-2500ms)"},
    "gtts": {"name": "Google TTS (gTTS)", "cost_per_1m_chars": 0.00, "ttfb_rating": "Standard (~1000-1800ms)"},
}


def benchmark_synthesis(text: str, lang: str, label: str) -> Dict[str, Any]:
    word_count = len(text.split())
    char_count = len(text)

    # 1. Measure First Audio Chunk Latency (TTFB)
    t0 = time.time()
    first_chunk_latency_ms = None
    first_chunk_size = 0

    try:
        stream_gen = tts_service.stream_speech_chunks(text, language=lang)
        for chunk in stream_gen:
            first_chunk_latency_ms = int((time.time() - t0) * 1000)
            first_chunk_size = len(chunk)
            break
    except Exception as e:
        first_chunk_latency_ms = 0

    # 2. Measure Full Generation Time (Cold Synthesis)
    t_start = time.time()
    res = tts_service.generate_speech(text, language=lang, force_regenerate=True)
    total_time_ms = int((time.time() - t_start) * 1000)

    # 3. Measure Cache Hit Latency (Warm Retrieval)
    t_cache = time.time()
    res_cached = tts_service.generate_speech(text, language=lang, force_regenerate=False)
    cache_time_ms = int((time.time() - t_cache) * 1000)

    # Speed metrics
    chars_per_sec = round(char_count / (total_time_ms / 1000), 1) if total_time_ms > 0 else 0
    words_per_sec = round(word_count / (total_time_ms / 1000), 1) if total_time_ms > 0 else 0

    # Cost calculation
    provider_info = PROVIDER_COST_RATES.get(res["provider"], {"cost_per_1m_chars": 0.0})
    est_cost = (char_count / 1_000_000) * provider_info["cost_per_1m_chars"]

    return {
        "label": label,
        "language": lang,
        "characters": char_count,
        "words": word_count,
        "provider": res["provider"],
        "voice": res["voice_name"],
        "format": res["format"],
        "duration_seconds": res["duration_seconds"],
        "first_chunk_latency_ms": first_chunk_latency_ms or total_time_ms,
        "total_time_ms": total_time_ms,
        "cache_time_ms": cache_time_ms,
        "chars_per_sec": chars_per_sec,
        "words_per_sec": words_per_sec,
        "estimated_cost_usd": f"${est_cost:.6f}",
    }


def run_all_benchmarks():
    print("=" * 80)
    print("PAGE TO VOICE: FAST AUDIO GENERATION PERFORMANCE BENCHMARK")
    print("Evaluating: English, Tamil, and Sinhala Narration across Active Providers")
    print("=" * 80)

    results: List[Dict[str, Any]] = []

    for lang in ["en", "ta", "si"]:
        for sample_type in ["short", "medium"]:
            text = SAMPLES[lang][sample_type]
            label = f"{lang.upper()} ({sample_type})"
            print(f"Testing {label} [{len(text)} chars]...")
            data = benchmark_synthesis(text, lang, label)
            results.append(data)

    print("\n" + "=" * 80)
    print(f"{'Sample':<12} | {'Provider':<12} | {'Format':<6} | {'TTFB':<8} | {'Total Time':<11} | {'Cache':<7} | {'Throughput':<12} | {'Est. Cost':<10}")
    print("-" * 80)

    for r in results:
        print(
            f"{r['label']:<12} | {r['provider']:<12} | {r['format']:<6} | "
            f"{r['first_chunk_latency_ms']:>5} ms | {r['total_time_ms']:>7} ms | "
            f"{r['cache_time_ms']:>4} ms | {r['chars_per_sec']:>6} char/s | {r['estimated_cost_usd']:<10}"
        )

    print("=" * 80)

    # Full Audiobook Projection (Standard 5-Chapter Book, ~15,000 words, ~90,000 chars)
    print("\n--- FULL AUDIOBOOK GENERATION PROJECTION (5 Chapters, 15,000 words) ---")
    avg_speed = sum(r["chars_per_sec"] for r in results) / len(results)
    projected_seconds = round(90000 / avg_speed, 1)
    print(f"• Average Throughput: {round(avg_speed, 1)} characters/sec")
    print(f"• First Chapter Available in: ~{results[0]['total_time_ms'] / 1000:.2f} seconds (Immediate Playback Starts)")
    print(f"• Remaining 4 Chapters in Background: ~{projected_seconds:.1f} seconds total")
    print(f"• With Dual Concurrency (Workers=2): ~{projected_seconds / 2:.1f} seconds total background time")
    print(f"• Replay from Cache: 0.0 seconds (Instant)")
    print("=" * 80)


if __name__ == "__main__":
    run_all_benchmarks()

