"""Processus jetable, borné en mémoire/CPU sur Linux."""
import io
import json
import sys
from html.parser import HTMLParser

class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden, self.parts = 0, []
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "head"}:
            self.hidden += 1
        if not self.hidden and tag in {"p", "br", "h1", "h2", "h3", "li", "div"}:
            self.parts.append("\n\n")
    def handle_endtag(self, tag):
        if tag in {"script", "style", "nav", "head"}:
            self.hidden = max(0, self.hidden - 1)
    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

def main():
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    data = sys.stdin.buffer.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("size")
    mime = sys.argv[1]
    pages = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    profile = sys.argv[3] if len(sys.argv)>3 else "full"
    if profile not in {"full","science_2023_cm"}:raise ValueError("profile")
    if mime == "application/pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted or len(reader.pages) > 100:
            raise ValueError("pdf")
        selected = [reader.pages[index-1] for index in pages] if pages else reader.pages
        result = "\n\n".join(page.extract_text() or "" for page in selected)
        if profile=="science_2023_cm":
            from shared.science.source_extract import cm_extract
            result=cm_extract(data,reader,pages)
    elif mime in {"text/html", "text/plain", "text/markdown"}:
        if profile!="full":raise ValueError("Profil réservé au PDF vérifié")
        if pages:
            raise ValueError("Pages réservées aux PDF")
        result = data.decode("utf-8-sig", errors="strict")
        if mime == "text/html":
            parser = TextHTML()
            parser.feed(result)
            result = "".join(parser.parts)
    else:
        raise ValueError("mime")
    if len(result) > 100_000:
        raise ValueError("text")
    sys.stdout.buffer.write(result.encode("utf-8"))

if __name__ == "__main__":
    main()
