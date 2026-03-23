# Documentation

This folder contains comprehensive documentation for the Restaurant Inspector API system.

## Documents

### 1. [Architecture](architecture.md)
**High-level system architecture** showing the complete infrastructure, components, and their relationships.

Topics covered:
- Client layer and API endpoints
- HF Spaces infrastructure
- FastAPI server components
- Model pipeline and AI processing
- Hugging Face Hub integration
- Data flow and design decisions
- Scalability and monitoring

**Diagram**: `architecture-diagram.png`

---

### 2. [Request Flow](flow.md)
**Detailed sequence diagram** showing the complete lifecycle of a review analysis request.

Topics covered:
- Startup phase (model download and loading)
- Request processing (per review)
- Tokenization process
- Model inference steps
- Response generation
- Performance metrics and latency breakdown
- Error handling
- Optimization opportunities

**Diagram**: `flow-diagram.png`

---

### 3. [System Components](system-components.md)
**Component-level breakdown** of both training pipeline (offline) and production API (live).

Topics covered:
- Training Pipeline:
  - Yelp dataset
  - training script (train.py)
  - Rule-based labeling
  - DistilBERT fine-tuning
  - Model artifacts
  - HF Hub upload
  
- Production API:
  - main.py structure
  - Model download mechanism
  - FastAPI endpoints
  - Transformers pipeline
  - JSON response formatting
  
- Technology stack and file structure

**Diagram**: `system-components-diagram.png`

---

### 4. [Mermaid Syntax](mermaid-syntax.md)
Raw Mermaid diagram code for all three architecture diagrams. Use this to:
- Regenerate diagrams
- Customize visualizations
- Create variations
- Render in Markdown viewers

---

## Diagrams

Place the architecture diagram images in this folder:

- `architecture-diagram.png` - High-level system architecture
- `flow-diagram.png` - Request flow sequence
- `system-components-diagram.png` - Training & production components

These images complement the Mermaid code blocks in each document.

---

## Viewing

### Locally
Open any `.md` file in VS Code, GitHub Desktop, or any Markdown viewer.

### GitHub
Push to GitHub and view in the repository. Mermaid diagrams render automatically in GitHub Markdown.

```bash
# Example: Push docs to GitHub
git add docs/
git commit -m "Add comprehensive architecture documentation"
git push origin main
```

### Online Mermaid Editors
- [Mermaid Live Editor](https://mermaid.live/)
- [Mermaid Chart](https://www.mermaidchart.com/)

Copy syntax from `mermaid-syntax.md` to edit diagrams.

---

## API Documentation

For interactive API documentation, visit:
- **Swagger UI**: https://dpratapx-restaurant-inspector-api-dev.hf.space/docs
- **ReDoc**: https://dpratapx-restaurant-inspector-api-dev.hf.space/redoc

---

## Contributing

To update documentation:

1. Edit the relevant `.md` file
2. Update Mermaid syntax in `mermaid-syntax.md` if diagrams change
3. Regenerate diagram images if needed
4. Commit and push changes

---

## License

This documentation is part of the Restaurant Inspector project.
