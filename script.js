document.addEventListener("DOMContentLoaded", () => {
  // EMAILJS
  const form = document.getElementById("contact-form");

  if (form && typeof emailjs !== "undefined") {
    emailjs.init({
      publicKey: "TU_PUBLIC_KEY"
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const submitBtn = document.getElementById("submit-btn");
      const success = document.getElementById("form-success");
      const error = document.getElementById("form-error");

      if (success) success.hidden = true;
      if (error) error.hidden = true;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando...";
      }

      try {
        await emailjs.sendForm(
          "service_9bi0mzr",
          "template_84dgfno",
          form
        );

        if (success) success.hidden = false;
        form.reset();
      } catch (err) {
        console.error("Error EmailJS:", err);
        if (error) error.hidden = false;
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Enviar mensaje";
        }
      }
    });
  }

  // BLOG
  loadBlogPosts();
});

async function loadBlogPosts() {
  try {
    const response = await fetch("./blog-posts.json");

    if (!response.ok) {
      throw new Error("No se pudo cargar blog-posts.json");
    }

    const posts = await response.json();

    const previewContainer = document.getElementById("blog-preview-grid");
    const blogContainer =
      document.getElementById("blog-index") ||
      document.getElementById("blog-posts") ||
      document.getElementById("blog-grid");

    if (previewContainer) {
      previewContainer.innerHTML = posts
        .slice(0, 3)
        .map(createPostCard)
        .join("");
    }

    if (blogContainer) {
      blogContainer.innerHTML = posts
        .map(createPostCard)
        .join("");
    }
  } catch (error) {
    console.error("Error cargando el blog:", error);

    const previewContainer = document.getElementById("blog-preview-grid");
    const blogContainer =
      document.getElementById("blog-index") ||
      document.getElementById("blog-posts") ||
      document.getElementById("blog-grid");

    const errorMessage = `<p>No se han podido cargar las entradas del blog.</p>`;

    if (previewContainer) previewContainer.innerHTML = errorMessage;
    if (blogContainer) blogContainer.innerHTML = errorMessage;
  }
}

function createPostCard(post) {
  const title = post.title || post.titulo || "Entrada sin título";
  const date = post.date || post.fecha || "";
  const excerpt = post.excerpt || post.resumen || post.description || "";
  const url = post.url || post.href || post.link || "#";

  return `
    <article class="blog-card">
      <p class="eyebrow">${date}</p>
      <h3>${title}</h3>
      <p>${excerpt}</p>
      <a href="${url}">Leer entrada →</a>
    </article>
  `;
}

// MODALES
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.showModal();
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.close();
}
