import os
import requests
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, session
from urllib.parse import urlparse
import base64
import json
import secrets

from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/index', methods=['POST'])
def api_generate_readme():
    try:
        repo_url = request.json.get('repo_url')
        if not repo_url:
            return jsonify({'success': False, 'error': 'Repository URL is required'}), 400
        if 'github.com' not in repo_url:
            return jsonify({'success': False, 'error': 'Please provide a valid GitHub repository URL'}), 400

        repo_name = repo_url.rstrip('/').split('/')[-1]
        prompt = f"""Generate a professional README.md for a GitHub repository named {repo_name}.\nURL: {repo_url}\n\nInclude these sections:\n1. Project Title and Description\n2. Features\n3. Installation Guide\n4. Usage Instructions\n5. Contributing Guidelines\n6. License Information\n\nFormat it in clean Markdown without any code block markers or explanatory text.\nMake it professional and comprehensive."""

        response = model.generate_content(prompt)
        readme_content = response.text.strip()
        if readme_content.startswith('```'):
            readme_content = readme_content.split('```')[1]
        if readme_content.endswith('```'):
            readme_content = readme_content.rsplit('```', 1)[0]

        return jsonify({
            'success': True,
            'readme': readme_content,
            'repo_info': {
                'name': repo_name,
                'description': 'Generated README',
                'language': 'N/A',
                'stars': 0,
                'forks': 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to generate README: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
    
    def get_important_files(self):
        """Get content of important files for analysis"""
        important_files = {}
        
        # Get package files
        package_files = [
            'package.json', 'requirements.txt', 'Gemfile', 'composer.json',
            'pom.xml', 'build.gradle', 'Cargo.toml', 'go.mod'
        ]
        
        # Get main code files (first few)
        try:
            tree = self.get_file_tree()
            code_files = []
            
            for item in tree['tree']:
                if item['type'] == 'blob':
                    path = item['path']
                    # Skip certain directories and files
                    if any(skip in path.lower() for skip in ['node_modules', '.git', 'dist', 'build', 'vendor']):
                        continue
                    
                    # Prioritize certain file types
                    if any(path.endswith(ext) for ext in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']):
                        code_files.append(path)
                    
                    # Check for package files
                    if any(pf in path for pf in package_files):
                        important_files[path] = self.get_file_content(path)
            
            # Get first few code files
            for file_path in code_files[:5]:  # Limit to first 5 files
                content = self.get_file_content(file_path)
                if content:
                    important_files[file_path] = content[:2000]  # Limit content length
                    
        except Exception as e:
            print(f"Error getting files: {e}")
        
        return important_files

class ReadmeGenerator:
    def __init__(self):
        self.model = model
    
    def generate_readme(self, repo_info, file_contents):
        """Generate README content using Gemini"""
        
        # Create a comprehensive prompt
        prompt = f"""
Based on the following GitHub repository information, generate a comprehensive and professional README.md file:

**Repository Information:**
- Name: {repo_info.get('name', 'N/A')}
- Description: {repo_info.get('description', 'No description provided')}
- Language: {repo_info.get('language', 'Not specified')}
- Stars: {repo_info.get('stargazers_count', 0)}
- Forks: {repo_info.get('forks_count', 0)}
- License: {repo_info.get('license', {}).get('name', 'Not specified') if repo_info.get('license') else 'Not specified'}

**File Contents Analysis:**
"""
        
        for file_path, content in file_contents.items():
            prompt += f"\n**{file_path}:**\n```\n{content[:1000]}...\n```\n"
        
        prompt += """

IMPORTANT: Return ONLY the raw Markdown content for the README.md file. Do not include any explanatory text, code block markers (```), or additional commentary. Start directly with the README content.

Generate a comprehensive README.md that includes:
1. Project title and description
2. Features (inferred from the code)
3. Installation instructions
4. Usage examples
5. Contributing guidelines
6. License information
7. Any other relevant sections

Output should be pure Markdown that can be directly saved as README.md file.
"""

        try:
            response = self.model.generate_content(prompt)
            readme_content = response.text
            
            # Clean up the response - remove any code block markers or explanatory text
            readme_content = readme_content.strip()
            
            # Remove markdown code block markers if present
            if readme_content.startswith('```markdown'):
                readme_content = readme_content[11:]  # Remove ```markdown
            elif readme_content.startswith('```'):
                readme_content = readme_content[3:]   # Remove ```
            
            if readme_content.endswith('```'):
                readme_content = readme_content[:-3]  # Remove closing ```
            
            # Remove any leading explanatory text before the actual README
            lines = readme_content.split('\n')
            start_idx = 0
            
            # Look for the first line that looks like a README title
            for i, line in enumerate(lines):
                if line.startswith('#') or line.strip().upper().startswith('README') or any(keyword in line.lower() for keyword in ['project', 'repository', 'application']):
                    start_idx = i
                    break
            
            readme_content = '\n'.join(lines[start_idx:]).strip()
            
            return readme_content
        except Exception as e:
            return f"Error generating README: {str(e)}"


# Serve frontend for GET requests (for Vercel static hosting)
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Vercel expects API at /api/index (POST)
@app.route('/api/index', methods=['POST'])
def api_generate_readme():
    try:
        repo_url = request.json.get('repo_url')
        if not repo_url:
            return jsonify({'success': False, 'error': 'Repository URL is required'}), 400
        if 'github.com' not in repo_url:
            return jsonify({'success': False, 'error': 'Please provide a valid GitHub repository URL'}), 400
        analyzer = GitHubRepoAnalyzer(repo_url)
        repo_info = analyzer.get_repo_info()
        file_contents = analyzer.get_important_files()
        generator = ReadmeGenerator()
        readme_content = generator.generate_readme(repo_info, file_contents)
        return jsonify({
            'success': True,
            'readme': readme_content,
            'repo_info': {
                'name': repo_info.get('name'),
                'description': repo_info.get('description'),
                'language': repo_info.get('language'),
                'stars': repo_info.get('stargazers_count'),
                'forks': repo_info.get('forks_count')
            }
        })
    except Exception as e:
        # Always return JSON error
        return jsonify({'success': False, 'error': str(e)}), 500

# For Vercel deployment
app = app

if __name__ == '__main__':
    app.run(debug=True)