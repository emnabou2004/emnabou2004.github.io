from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import markdown2
from datetime import datetime

app = Flask(__name__, static_folder='public', static_url_path='', template_folder='public')

BASE_DIR = Path(__file__).resolve().parent
POSTS_DIR = BASE_DIR / 'content' / 'posts'
PDFS_DIR = BASE_DIR / 'content' / 'pdfs'
UPLOAD_DIR = BASE_DIR / 'tmp'

POSTS_DIR.mkdir(parents=True, exist_ok=True)
PDFS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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


def slugify(title: str) -> str:
    slug = ''.join(ch.lower() if ch.isalnum() else '-' for ch in title).strip('-')
    return slug or 'note'


def get_post_files():
    return sorted(
        [p for p in POSTS_DIR.glob('*.md')],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def get_post_metadata(post_path: Path):
    text = post_path.read_text(encoding='utf-8')
    frontmatter, _ = parse_frontmatter(text)
    slug = post_path.stem
    return {
        'slug': slug,
        'title': frontmatter.get('title', slug.replace('-', ' ').title()),
        'description': frontmatter.get('description', ''),
        'date': frontmatter.get('date', post_path.stat().st_mtime),
        'category': frontmatter.get('category', 'blog')
    }


def get_post_payload(post_path: Path):
    text = post_path.read_text(encoding='utf-8')
    frontmatter, body = parse_frontmatter(text)
    slug = post_path.stem
    html = markdown2.markdown(body, extras=['fenced-code-blocks', 'tables', 'strike'])
    return {
        'slug': slug,
        'title': frontmatter.get('title', slug.replace('-', ' ').title()),
        'description': frontmatter.get('description', ''),
        'date': frontmatter.get('date', post_path.stat().st_mtime),
        'category': frontmatter.get('category', 'blog'),
        'content': html
    }


@app.get('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.get('/posts/<slug>')
def post_page(slug):
    return send_from_directory(app.static_folder, 'post.html')


@app.get('/api/posts')
def list_posts():
    return jsonify([get_post_metadata(path) for path in get_post_files()])


@app.post('/api/posts')
def create_post():
    payload = request.get_json(silent=True) or {}
    title = (payload.get('title') or '').strip()
    content = (payload.get('content') or '').strip()
    if not title or not content:
        return jsonify({'error': 'A title and content are required.'}), 400

    slug = slugify(title)
    path = POSTS_DIR / f'{slug}.md'
    date = datetime.now().strftime('%Y-%m-%d')
    body = f"---\ntitle: {title}\ndescription: A math note.\ndate: {date}\n---\n\n{content}\n"
    path.write_text(body, encoding='utf-8')
    return jsonify({'success': True, 'slug': slug})


@app.get('/api/posts/<slug>')
def show_post(slug):
    post_path = POSTS_DIR / f'{slug}.md'
    if not post_path.exists():
        return jsonify({'error': 'Post not found'}), 404
    return jsonify(get_post_payload(post_path))


@app.get('/api/pdfs')
def list_pdfs():
    files = sorted(
        [p for p in PDFS_DIR.glob('*.pdf')],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return jsonify([
        {'name': path.name, 'path': f'/content/pdfs/{path.name}'}
        for path in files
    ])


@app.post('/api/upload')
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(uploaded_file.filename)
    if not filename:
        return jsonify({'error': 'Invalid filename'}), 400

    ext = Path(filename).suffix.lower()
    target_dir = PDFS_DIR if ext == '.pdf' else POSTS_DIR
    target_path = target_dir / filename
    uploaded_file.save(target_path)

    return jsonify({'success': True, 'file': filename, 'type': 'pdf' if ext == '.pdf' else 'markdown'})


@app.get('/content/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(PDFS_DIR, filename, as_attachment=False)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
