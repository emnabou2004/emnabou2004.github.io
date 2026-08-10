import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
POSTS_DIR = BASE_DIR / 'content' / 'posts'
PDFS_DIR = BASE_DIR / 'content' / 'pdfs'
PUBLIC_DIR = BASE_DIR / 'public'
DOCS_DIR = BASE_DIR / 'docs'


def parse_frontmatter(text: str):
    if not text.startswith('---\n'):
        return {}, text
    parts = text.split('\n---\n', 1)
    if len(parts) != 2:
        return {}, text
    frontmatter = {}
    for line in parts[0].splitlines()[1:]:
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter, parts[1]


def build_posts():
    posts = []
    for post_path in sorted(POSTS_DIR.glob('*.md')):
        text = post_path.read_text(encoding='utf-8')
        frontmatter, _ = parse_frontmatter(text)
        slug = post_path.stem
        posts.append({
            'slug': slug,
            'title': frontmatter.get('title', slug.replace('-', ' ')),
            'description': frontmatter.get('description', ''),
            'date': frontmatter.get('date', ''),
            'category': frontmatter.get('category', 'blog')
        })
    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts


def build_pdfs():
    pdfs = []
    for pdf_path in sorted(PDFS_DIR.glob('*.pdf')):
        pdfs.append({
            'name': pdf_path.name,
            'path': f'content/pdfs/{pdf_path.name}'
        })
    return pdfs


def main():
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True)

    shutil.copy(PUBLIC_DIR / 'index.html', DOCS_DIR / 'index.html')
    shutil.copy(PUBLIC_DIR / 'styles.css', DOCS_DIR / 'styles.css')

    app_js = (PUBLIC_DIR / 'app.js').read_text(encoding='utf-8')
    app_js = app_js.replace("fetch('/api/posts')", "fetch('posts.json')")
    app_js = app_js.replace("fetch('/api/pdfs')", "fetch('pdfs.json')")
    (DOCS_DIR / 'app.js').write_text(app_js, encoding='utf-8')

    (DOCS_DIR / 'posts.json').write_text(json.dumps(build_posts(), indent=2), encoding='utf-8')
    (DOCS_DIR / 'pdfs.json').write_text(json.dumps(build_pdfs(), indent=2), encoding='utf-8')

    pdfs_out_dir = DOCS_DIR / 'content' / 'pdfs'
    pdfs_out_dir.mkdir(parents=True)
    for pdf_path in PDFS_DIR.glob('*.pdf'):
        shutil.copy(pdf_path, pdfs_out_dir / pdf_path.name)

    print(f'Built static site into {DOCS_DIR}')


if __name__ == '__main__':
    main()
