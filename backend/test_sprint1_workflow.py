import io
import os
import sys
import requests
import fitz  # PyMuPDF
import docx

BASE_URL = "http://127.0.0.1:8000"

print("==================================================")
print("PAGE TO VOICE - SPRINT 1 WORKFLOW VERIFICATION")
print("==================================================")

# 1. Login
print("\n[Step 1] Logging in as default admin...")
login_res = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "admin@pagetovoice.com", "password": "1234@1234"},
)
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("-> Logged in successfully. Token acquired.")

# 2. Create test files: PDF, DOCX, TXT
os.makedirs("test_samples", exist_ok=True)

# 2a. English PDF with 2 chapters
pdf_path = "test_samples/sample_english_book.pdf"
doc = fitz.open()
page1 = doc.new_page()
page1.insert_text((50, 50), "Chapter 1: The Beginning of Voice\n\nOnce upon a time in a digital library, text dreamed of having a voice. Words on pages yearned to be spoken aloud so travelers and readers could listen on their journeys. This was the dawn of intelligent audiobook generation.")
page2 = doc.new_page()
page2.insert_text((50, 50), "Chapter 2: The Sound of Intelligence\n\nIn the second chapter, artificial intelligence and neural speech synthesis came together. Sentences gained melody, pause, and emotion. The transition from silent print to resonant speech was complete.")
doc.save(pdf_path)
doc.close()
print("-> Created sample PDF with chapters:", pdf_path)

# 2b. Sinhala TXT file
si_txt_path = "test_samples/sample_sinhala_book.txt"
si_content = """පරිච්ඡේදය 1: ආරම්භය

පොත කියවීමෙන් මිනිසා සම්පූර්ණ වේ. අපගේ පරිකල්පනය සහ දැනුම පුළුල් කිරීමට පොත්පත් මහත් සේ උපකාරී වේ. නවීන තාක්ෂණය මගින් දැන් ඕනෑම ලේඛනයක් ශ්‍රව්‍ය පොතක් බවට පත් කළ හැක.

පරිච්ඡේදය 2: තාක්ෂණික දියුණුව

කෘතිම බුද්ධිය හරහා පෙළ පිරිසිදු කර ස්වභාවික කටහඬකින් ශ්‍රවණය කිරීමට හැකිවීම අපූරු අත්දැකීමකි.
"""
with open(si_txt_path, "w", encoding="utf-8") as f:
    f.write(si_content)
print("-> Created sample Sinhala TXT:", si_txt_path)

# 2c. Tamil DOCX file
ta_docx_path = "test_samples/sample_tamil_book.docx"
docx_doc = docx.Document()
docx_doc.add_heading("அத்தியாயம் 1: குரலின் பயணம்", level=1)
docx_doc.add_paragraph("புத்தகம் வாசிப்பது ஒரு மனிதனை முழுமையாக்குகிறது. அறிவையும் கற்பனையையும் வளர்ப்பதற்கு வாசிப்பு மிக முக்கியமானது. பக்கங்களை குரலாக மாற்றும் இந்த தளம் புதிய வாசகர்களுக்கு மிகவும் பயனுள்ளதாக இருக்கும்.")
docx_doc.add_heading("அத்தியாயம் 2: நவீன தொழில்நுட்பம்", level=1)
docx_doc.add_paragraph("செயற்கை நுண்ணறிவு மூலம் உரைகளை இயற்கை குரலில் மாற்றி கேட்கும் வசதி இங்கே வழங்கப்படுகிறது.")
docx_doc.save(ta_docx_path)
print("-> Created sample Tamil DOCX:", ta_docx_path)

# 3. Test Uploading PDF
print("\n[Step 2] Uploading English PDF...")
with open(pdf_path, "rb") as f:
    upload_res = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        files={"file": ("sample_english_book.pdf", f, "application/pdf")},
    )
assert upload_res.status_code == 201, f"PDF upload failed: {upload_res.text}"
pdf_doc_data = upload_res.json()
pdf_doc_id = pdf_doc_data["id"]
print(f"-> Uploaded PDF Document #{pdf_doc_id}: {pdf_doc_data['title']} (Status: {pdf_doc_data['status']})")

# 4. Test Processing PDF
print(f"\n[Step 3] Processing PDF Document #{pdf_doc_id}...")
process_res = requests.post(f"{BASE_URL}/api/documents/{pdf_doc_id}/process", headers=headers)
assert process_res.status_code == 200, f"Processing failed: {process_res.text}"
process_data = process_res.json()
print(f"-> Processed PDF successfully: Detected Language='{process_data['detected_language']}', Chapters={process_data['chapter_count']}")

# Fetch chapters
chapters_res = requests.get(f"{BASE_URL}/api/documents/{pdf_doc_id}/chapters", headers=headers)
assert chapters_res.status_code == 200
chapters = chapters_res.json()
for c in chapters:
    print(f"   * Chapter {c['chapter_number']}: '{c['title']}' (Length: {len(c['processed_text'])} chars)")

# 5. Test Uploading & Processing Sinhala TXT
print("\n[Step 4] Uploading & Processing Sinhala TXT...")
with open(si_txt_path, "rb") as f:
    si_upload_res = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        files={"file": ("sample_sinhala_book.txt", f, "text/plain")},
    )
assert si_upload_res.status_code == 201
si_doc_id = si_upload_res.json()["id"]

si_process_res = requests.post(f"{BASE_URL}/api/documents/{si_doc_id}/process", headers=headers)
assert si_process_res.status_code == 200
si_pdata = si_process_res.json()
print(f"-> Processed Sinhala Document #{si_doc_id}: Detected Language='{si_pdata['detected_language']}', Chapters={si_pdata['chapter_count']}")

# 6. Test Uploading & Processing Tamil DOCX
print("\n[Step 5] Uploading & Processing Tamil DOCX...")
with open(ta_docx_path, "rb") as f:
    ta_upload_res = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        files={"file": ("sample_tamil_book.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
assert ta_upload_res.status_code == 201
ta_doc_id = ta_upload_res.json()["id"]

ta_process_res = requests.post(f"{BASE_URL}/api/documents/{ta_doc_id}/process", headers=headers)
assert ta_process_res.status_code == 200
ta_pdata = ta_process_res.json()
print(f"-> Processed Tamil Document #{ta_doc_id}: Detected Language='{ta_pdata['detected_language']}', Chapters={ta_pdata['chapter_count']}")

# 7. Test AI Clean Text
sample_chap = chapters[0]
print(f"\n[Step 6] Testing Gemini AI Clean Text on Chapter 1...")
clean_res = requests.post(
    f"{BASE_URL}/api/ai/clean-text",
    headers=headers,
    json={"text": sample_chap["original_text"] + " [Footnote: 12] (see page 4)", "language": "en", "chapter_id": sample_chap["id"]},
)
assert clean_res.status_code == 200
print("-> Cleaned Text Preview:", clean_res.json()["cleaned_text"][:120], "...")

# 8. Test AI Summarization
print(f"\n[Step 7] Testing Gemini AI Summarization on Chapter 1...")
sum_res = requests.post(
    f"{BASE_URL}/api/ai/summarize",
    headers=headers,
    json={"text": sample_chap["original_text"], "language": "en", "chapter_id": sample_chap["id"]},
)
assert sum_res.status_code == 200
print("-> Chapter Summary Preview:", sum_res.json()["summary"][:120], "...")

# 9. Test AI Translation (English -> Tamil)
print(f"\n[Step 8] Testing Gemini AI Translation (EN -> TA)...")
trans_res = requests.post(
    f"{BASE_URL}/api/ai/translate",
    headers=headers,
    json={"text": "Text to speech gives books a voice.", "source_language": "en", "target_language": "ta"},
)
assert trans_res.status_code == 200
print("-> Translated to Tamil:", trans_res.json()["translated_text"])

# 10. Test TTS Generation on English Chapter
print(f"\n[Step 9] Testing TTS Generation on English Chapter 1...")
tts_res = requests.post(
    f"{BASE_URL}/api/tts/generate",
    headers=headers,
    json={"chapter_id": sample_chap["id"], "language": "en"},
)
assert tts_res.status_code == 200
tts_data = tts_res.json()
print(f"-> Audio Generated successfully: URL={tts_data['audio_url']}, Duration={tts_data['duration_seconds']}s, Provider={tts_data['provider']}")

# 11. Test Audio File Streaming
audio_url = f"{BASE_URL}{tts_data['audio_url']}"
print(f"\n[Step 10] Testing Audio Streaming ({audio_url})...")
stream_res = requests.get(audio_url)
assert stream_res.status_code == 200
assert len(stream_res.content) > 1000
print(f"-> Audio Stream verified! Content-Type='{stream_res.headers.get('content-type')}', Received {len(stream_res.content)} bytes.")

print("\n==================================================")
print("ALL SPRINT 1 WORKFLOW REQUIREMENTS VERIFIED SUCCESSFULLY!")
print("==================================================")

