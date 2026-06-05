function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.showModal();
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.close();
}

document.addEventListener('click', (e) => {
  if (e.target.tagName === 'DIALOG') e.target.close();
});


// CARGA DE ENTRADAS EN LA PÁGINA PRINCIPAL
fetch('blog-posts.json?v=' + Date.now())
  .then(r => r.json())
  .then(posts => {
    const grid = document.getElementById('blog-preview-grid');
    if (!grid) return;

    const recientes = posts.slice(0, 3);

    if (!recientes.length) {
      grid.innerHTML = '<p style="color:var(--muted)">Aún no hay artículos.</p>';
      return;
    }

    grid.innerHTML = recientes.map(p => `
      <article class="blog-preview-card${p.imagen ? ' has-imagen' : ''}" onclick="location.href='blog-articulo.html?id=${p.id}'" style="cursor:pointer">
        ${p.imagen ? `<img src="${p.imagen}" alt="${p.titulo}" class="blog-preview-img" />` : ''}
        <div class="blog-preview-body">
          <span class="blog-date">${p.fecha}</span>
          <h3>${p.titulo}</h3>
          <p>${p.extracto}</p>
          <a href="blog-articulo.html?id=${p.id}" class="blog-read-more">Leer →</a>
        </div>
      </article>
    `).join('');
  })
  .catch(error => {
    console.error('Error cargando entradas recientes:', error);
  });


// EMAILJS
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('contact-form');

  if (!form) return;

  if (typeof emailjs === 'undefined') {
    console.warn('EmailJS no está cargado en esta página.');
    return;
  }

  emailjs.init({
    publicKey: 'XsTpXPWBRSuuZA0Pn'
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const submitBtn = document.getElementById('submit-btn');
    const success = document.getElementById('form-success');
    const error = document.getElementById('form-error');

    if (success) success.hidden = true;
    if (error) error.hidden = true;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Enviando...';
    }

    try {
      await emailjs.sendForm(
        'service_9bi0mzr',
        'template_84dgfno',
        form
      );

      if (success) success.hidden = false;
      form.reset();
    } catch (err) {
      console.error('Error EmailJS:', err);
      if (error) error.hidden = false;
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Enviar mensaje';
      }
    }
  });
});


// ÍNDICE DEL BLOG
function cargarIndiceBlog() {
  const indexList = document.getElementById('blog-index-list');

  if (!indexList) return;

  fetch('blog-posts.json?v=' + Date.now())
    .then(response => {
      if (!response.ok) {
        throw new Error('No se pudo cargar blog-posts.json');
      }

      return response.json();
    })
    .then(posts => {
      if (!Array.isArray(posts) || posts.length === 0) {
        indexList.innerHTML = '<p style="color:var(--muted)">Aún no hay entradas publicadas.</p>';
        return;
      }

      indexList.innerHTML = posts.map(post => `
        <a class="blog-index-link" href="blog-articulo.html?id=${encodeURIComponent(post.id)}">
          <span>${post.fecha}</span>
          <strong>${post.titulo}</strong>
        </a>
      `).join('');
    })
    .catch(error => {
      console.error('Error cargando índice del blog:', error);
      indexList.innerHTML = '<p style="color:var(--muted)">No se pudo cargar el índice del blog.</p>';
    });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', cargarIndiceBlog);
} else {
  cargarIndiceBlog();
}
