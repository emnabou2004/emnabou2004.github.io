function renderCard(post, pdfs) {
  const pdf = pdfs.find((item) => item.name === post.pdf);
  const titleHtml = pdf
    ? `<a href="${pdf.path}" target="_blank" rel="noopener">${post.title}</a>`
    : post.title;
  return `
    <div class="card">
      <div class="card-head">
        <h3>${titleHtml}</h3>
        <p class="post-date">${post.date}</p>
      </div>
      ${post.description ? `<p>${post.description}</p>` : ''}
    </div>
  `;
}

function renderList(host, posts, pdfs) {
  host.innerHTML = posts.length
    ? posts.map((post) => renderCard(post, pdfs)).join('')
    : '<p>No posts yet.</p>';
}

async function loadContent() {
  const projectsHost = document.getElementById('posts-list');
  const blogHost = document.getElementById('blog-posts-list');
  const [postsRes, pdfsRes] = await Promise.all([fetch('/api/posts'), fetch('/api/pdfs')]);
  const posts = await postsRes.json();
  const pdfs = await pdfsRes.json();

  const projectPosts = posts.filter((post) => post.category === 'projects');
  const blogPosts = posts.filter((post) => post.category !== 'projects');

  renderList(projectsHost, projectPosts, pdfs);
  renderList(blogHost, blogPosts, pdfs);
}

const editorForm = document.getElementById('editor-form');
if (editorForm) {
  editorForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const title = document.getElementById('post-title').value.trim();
    const content = document.getElementById('post-content').value.trim();

    if (!title || !content) {
      return;
    }

    const response = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content })
    });

    const result = await response.json();
    if (result.success) {
      editorForm.reset();
      loadContent();
    }
  });
}

const uploadForm = document.getElementById('upload-form');
if (uploadForm) {
  uploadForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(uploadForm);
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const result = await response.json();
    if (result.success) {
      uploadForm.reset();
    }
  });
}

loadContent();
