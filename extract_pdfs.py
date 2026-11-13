import PyPDF2

try:
    with open('pdfs.txt', 'w', encoding='utf-8') as out:
        try:
            reader1 = PyPDF2.PdfReader(r'C:\Users\hp\.gemini\antigravity\brain\dc5d38c7-de50-4439-a2eb-5b857a17c7c6\.user_uploaded\media_1788320925260.pdf')
            for i, p in enumerate(reader1.pages):
                out.write(f"--- PDF 1 PAGE {i} ---\n")
                out.write(p.extract_text() + "\n")
        except Exception as e:
            out.write(f"Error PDF1: {e}\n")
            
        try:
            reader2 = PyPDF2.PdfReader(r'C:\Users\hp\.gemini\antigravity\brain\dc5d38c7-de50-4439-a2eb-5b857a17c7c6\.user_uploaded\media_1788430930758.pdf')
            for i, p in enumerate(reader2.pages):
                out.write(f"--- PDF 2 PAGE {i} ---\n")
                out.write(p.extract_text() + "\n")
        except Exception as e:
            out.write(f"Error PDF2: {e}\n")
    print("Extracted successfully.")
except Exception as e:
    print("Main error:", e)
