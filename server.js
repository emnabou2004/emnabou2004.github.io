const express = require('express');
const fs = require('fs');
const path = require('path');
const multer = require('multer');
const { marked } = require('marked');
const katex = require('katex');

const app = express();
const port = process.env.PORT || 3000;

const rootDir = __dirname;
const postsDir = path.join(rootDir, 'content', 'posts');
const pdfsDir = path.join(rootDir, 'content', 'pdfs');

if (!fs.existsSync(postsDir)) fs.mkdirSync(postsDir, { recursive: true });
if (!fs.existsSync(pdfsDir)) fs.mkdirSync(pdfsDir, { recursive: true });

const upload = multer({ dest: path.join(rootDir, 'tmp') });

app.use(express.static(path.join(rootDir, 'public')));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

function readMarkdownFile(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const match = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$/);

  if (!match) {
    return { frontmatter: {}, body: raw };
  }

  const frontmatter = Object.fromEntries(
    match[1]
      .split('\n')
      .filter(Boolean)
      .map((line) => {
        const [key, ...valueParts] = line.split(':');
        return [key.trim(), valueParts.join(':').trim()];
      })
  );

  return { frontmatter, body: match[2] || '' };
}

function getPostFiles() {
  return fs
    .readdirSync(postsDir)
    .filter((name) => name.toLowerCase().endsWith('.md'))
    .sort((a, b) => fs.statSync(path.join(postsDir, b)).mtimeMs - fs.statSync(path.join(postsDir, a)).mtimeMs);
}

function getPostData(fileName) {
  const filePath = path.join(postsDir, fileName);
  const { frontmatter, body } = readMarkdownFile(filePath);
  const slug = path.basename(fileName, path.extname(fileName));
  return {
    slug,
    title: frontmatter.title || slug.replace(/-/g, ' '),
    description: frontmatter.description || 'A math note.',
    date: frontmatter.date || new Date(fs.statSync(filePath).mtimeMs).toISOString().slice(0, 10),
    category: frontmatter.category || 'blog',
    content: renderMarkdown(body)
  };
}

function renderMarkdown(markdown) {
  const replacements = [];
  const mathPattern = /\$\$([\s\S]+?)\$\$|\$([^$]+?)\$/g;

  const withMath = markdown.replace(mathPattern, (full, display, inline) => {
    const source = display || inline;
    const displayMode = Boolean(display);
    const token = `__MATH_${replacements.length}__`;
    try {
      replacements.push(katex.renderToString(source, { throwOnError: false, displayMode }));
    } catch (error) {
      replacements.push(`<code>${full}</code>`);
    }
    return token;
  });

  let html = marked.parse(withMath);
  html = html.replace(/__MATH_(\d+)__/g, (_, index) => replacements[Number(index)] || '');
  return html;
}

app.get('/', (req, res) => {
  res.sendFile(path.join(rootDir, 'public', 'index.html'));
});

app.get('/posts/:slug', (req, res) => {
  res.sendFile(path.join(rootDir, 'public', 'post.html'));
});

app.get('/api/posts', (req, res) => {
  const posts = getPostFiles().map((fileName) => {
    const filePath = path.join(postsDir, fileName);
    const { frontmatter } = readMarkdownFile(filePath);
    const slug = path.basename(fileName, path.extname(fileName));
    return {
      slug,
      title: frontmatter.title || slug.replace(/-/g, ' '),
      description: frontmatter.description || 'A math note.',
      date: frontmatter.date || new Date(fs.statSync(filePath).mtimeMs).toISOString().slice(0, 10),
      category: frontmatter.category || 'blog'
    };
  });
  res.json(posts);
});

app.get('/api/posts/:slug', (req, res) => {
  const targetFile = getPostFiles().find((fileName) => path.basename(fileName, path.extname(fileName)) === req.params.slug);
  if (!targetFile) {
    return res.status(404).json({ error: 'Post not found.' });
  }
  res.json(getPostData(targetFile));
});

app.get('/api/pdfs', (req, res) => {
  const pdfs = fs
    .readdirSync(pdfsDir)
    .filter((name) => name.toLowerCase().endsWith('.pdf'))
    .sort((a, b) => fs.statSync(path.join(pdfsDir, b)).mtimeMs - fs.statSync(path.join(pdfsDir, a)).mtimeMs)
    .map((fileName) => ({
      name: fileName,
      path: `/content/pdfs/${encodeURIComponent(fileName)}`
    }));
  res.json(pdfs);
});

app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file was received.' });
  }

  const ext = path.extname(req.file.originalname).toLowerCase();
  const targetDir = ext === '.pdf' ? pdfsDir : postsDir;
  const finalPath = path.join(targetDir, req.file.originalname);

  fs.renameSync(req.file.path, finalPath);

  res.json({ success: true, file: req.file.originalname, type: ext === '.pdf' ? 'pdf' : 'markdown' });
});

app.use('/content/pdfs', express.static(pdfsDir));

app.listen(port, () => {
  console.log(`Math blog running at http://localhost:${port}`);
});
