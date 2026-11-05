import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from services import azure_tts_service, tts_service


def test_azure_voice_resolution():
    print("--- Testing Azure Voice Resolution ---")
    voices_en = azure_tts_service.AVAILABLE_AZURE_VOICES["en"]
    voices_ta = azure_tts_service.AVAILABLE_AZURE_VOICES["ta"]
    voices_si = azure_tts_service.AVAILABLE_AZURE_VOICES["si"]

    assert len(voices_en) >= 2, "Expected at least 2 English neural voices"
    assert len(voices_ta) >= 2, "Expected at least 2 Tamil neural voices"
    assert len(voices_si) >= 2, "Expected at least 2 Sinhala neural voices"

    assert azure_tts_service.resolve_voice_name("en") == "en-US-JennyNeural"
    assert azure_tts_service.resolve_voice_name("ta") == "ta-IN-PallaviNeural"
    assert azure_tts_service.resolve_voice_name("si") == "si-LK-ThiliniNeural"
    assert azure_tts_service.resolve_voice_name("en", "en-US-GuyNeural") == "en-US-GuyNeural"
    print("✓ Voice resolution tests passed!")


def test_tts_service_voices_endpoint():
    print("--- Testing TTS Service Available Voices ---")
    voices_en = tts_service.get_available_voices("en")
    voices_ta = tts_service.get_available_voices("ta")
    voices_si = tts_service.get_available_voices("si")

    assert len(voices_en) > 0
    assert len(voices_ta) > 0
    assert len(voices_si) > 0
    print(f"✓ English voices ({len(voices_en)}), Tamil voices ({len(voices_ta)}), Sinhala voices ({len(voices_si)})")


def test_text_splitting_for_azure():
    print("--- Testing Text Splitting for Azure ---")
    short_text = "This is a short chapter introduction."
    chunks = azure_tts_service.split_text_for_azure(short_text)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    long_text = ("This is a great story about intelligence. " * 100) + "\n\n" + ("Second paragraph. " * 80)
    chunks_long = azure_tts_service.split_text_for_azure(long_text, max_chars=1000)
    assert len(chunks_long) > 1
    for c in chunks_long:
        assert len(c) <= 1200
    print(f"✓ Splitting long text into {len(chunks_long)} natural chunks verified!")


def test_tts_generation_and_fallback():
    print("--- Testing Speech Generation & Resilient Fallback ---")
    # Test English generation (with fallback if Azure key not supplied)
    res_en = tts_service.generate_speech("Welcome to Page to Voice audiobook generator.", language="en")
    print(f"✓ Generated English speech: provider={res_en['provider']}, format={res_en['format']}, url={res_en['audio_url']}")
    assert res_en["audio_url"]
    assert res_en["duration_seconds"] > 0

    # Test Tamil generation
    res_ta = tts_service.generate_speech("பேஜ் டு வாய்ஸ் இயங்குதளத்திற்கு வரவேற்கிறோம்.", language="ta")
    print(f"✓ Generated Tamil speech: provider={res_ta['provider']}, format={res_ta['format']}, url={res_ta['audio_url']}")
    assert res_ta["audio_url"]

    # Test Sinhala generation
    res_si = tts_service.generate_speech("පිටුවෙන් හඬට වේදිකාවට ඔබව සාදරයෙන් පිළිගනිමු.", language="si")
    print(f"✓ Generated Sinhala speech: provider={res_si['provider']}, format={res_si['format']}, url={res_si['audio_url']}")
    assert res_si["audio_url"]

    # Test Caching
    res_cached = tts_service.generate_speech("Welcome to Page to Voice audiobook generator.", language="en")
    print(f"✓ Cached speech response: cached={res_cached['cached']}, generation_time={res_cached['generation_time_ms']}ms")
    assert res_cached["cached"] is True


if __name__ == "__main__":
    test_azure_voice_resolution()
    test_tts_service_voices_endpoint()
    test_text_splitting_for_azure()
    test_tts_generation_and_fallback()
    print("\nALL AZURE TTS TESTS COMPLETED SUCCESSFULLY!")

