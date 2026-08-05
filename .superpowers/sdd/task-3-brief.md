### Task 3: Remover Bibliotecario IA

**Files:**
- Delete: `web/bibliotecario.html`
- Modify: `web/index.html`
- Modify: `README.md`

**Interfaces:** ninguna — independiente de las tasks anteriores.

- [ ] **Step 1: Borrar el prototipo**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git rm web/bibliotecario.html
```

- [ ] **Step 2: Sacar la card de `web/index.html`**

Eliminar este bloque completo:

```html
      <a href="bibliotecario.html" class="tool-card">
        <span class="tool-tag tag-ia">IA Documental</span>
        <h2>Bibliotecario IA</h2>
        <p>Consulta el corpus documental de CIGOB en lenguaje natural. Respuestas fundamentadas con citas de fuentes.</p>
        <ul class="tool-features">
          <li>RAG sobre documentos de CIGOB</li>
          <li>Citas automaticas por documento</li>
          <li>Responde sobre estrategia, IA y gestion</li>
          <li>Powered by Claude (Anthropic)</li>
        </ul>
        <span class="tool-link">Abrir Bibliotecario &rarr;</span>
      </a>

```

- [ ] **Step 3: Sacar la fila de `README.md` raíz**

Quitar de la tabla `## Web pública`:

```markdown
| `web/bibliotecario.html` | Prototipo del Bibliotecario IA (RAG sobre corpus CIGOB) — **en desarrollo, aún no funcional**; la API key se ingresa en runtime, no se versiona |
```

- [ ] **Step 4: Commit**

```bash
git add web/index.html README.md
git commit -m "chore: saca el prototipo Bibliotecario IA del repo"
```

---

