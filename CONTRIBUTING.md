# Contributing Guide

Thank you for your interest in contributing to Clinical Trials Matcher!

## How to Contribute

### Reporting Bugs

1. Check if the bug is already reported in [Issues](../../issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)

### Suggesting Features

1. Open an issue with tag `enhancement`
2. Describe the feature and why it would be useful
3. Provide examples or use cases if applicable

### Code Contributions

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Make** your changes
4. **Test** your changes locally
5. **Commit** with clear messages: `git commit -m 'Add feature: description'`
6. **Push** to your fork: `git push origin feature/your-feature`
7. **Open a Pull Request** with:
   - Clear description of changes
   - Link to related issues
   - Any breaking changes noted

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions
- Keep lines under 100 characters

### Testing

Before submitting a PR:
- Test locally with your changes
- Ensure API endpoints work correctly
- Check frontend renders properly
- Test with different patient data

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/clinical-trials-matcher.git
cd "Clinical Trials"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Neo4j credentials

# Run backend
uvicorn app.main:app --reload

# In another terminal, serve frontend
cd app/static
python -m http.server 8001
```

## Questions?

Feel free to open an issue or discussion for questions!
