

from flask import Flask, render_template_string, request, redirect, url_for, send_file, session, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import io
from zipfile import ZipFile
import logging
import shutil

# Import custom modules (Ensure these modules are correctly implemented in your project)
from utils.groq_integration import GroqClient
from utils.file_processing import extract_all_text
from utils.pdf_generation_reportlab import generate_individual_pdf_report, generate_compiled_pdf_report
from tools.compliance_checks import check_assessment_compliance, check_module_compliance
from tools.grammar_check import grammar_check
from tools.reference_check import reference_check
from tools.critical_writing_check import critical_writing_check

# Load environment variables from a .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # In production, use a fixed secret key.
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize GroqClient
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("🛑 GROQ_API_KEY not found. Please set it in the environment variables.")
groq_client = GroqClient(api_key=GROQ_API_KEY)

# HTML Templates as normal triple-quoted strings (no f-strings)
base_header = """
<header>
    <nav style="background-color: #f8f9fa; padding: 10px;">
        <a href="{{ url_for('home') }}" style="margin-right: 15px;">Home</a>
        <a href="{{ url_for('tutorial') }}" style="margin-right: 15px;">Tutorial</a>
        <a href="{{ url_for('reports') }}">Reports</a>
    </nav>
</header>
<hr>
"""

home_template = """
<!doctype html>
<html lang="en">
  <head>
    <title>Academic QA Assistant 📚</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 40px; }
      .container { max-width: 800px; margin: auto; }
      .error { color: red; }
      .success { color: green; }
      .section { margin-bottom: 30px; }
      .button { padding: 10px 20px; background-color: green; color: white; border: none; cursor: pointer; }
      .button:hover { background-color: darkgreen; }
      a { text-decoration: none; color: #007bff; }
      a:hover { text-decoration: underline; }
      .file-list { list-style-type: none; padding: 0; }
      .file-list li { margin-bottom: 5px; }
      .checkbox-group { margin-left: 20px; }
    </style>
  </head>
  <body>
    """ + base_header + """
    <div class="container">
      <h1>Academic QA Assistant 📚</h1>
      <h3>Automate Quality Assurance for Academic Assignments with AI 🧠</h3>
      <hr>
      
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          {% for category, message in messages %}
            <p class="{{ category }}">{{ message }}</p>
          {% endfor %}
        {% endif %}
      {% endwith %}
      
      <div class="section">
        <h2>📁 Upload Your Documents</h2>
        <form method="POST" action="{{ url_for('process_files') }}" enctype="multipart/form-data">
          <label>📄 Upload Student's Assignment (Max 5MB):</label><br>
          <input type="file" name="assignment_file" accept=".pdf,.docx,.pptx" required>
          {% if session.get('assignment_filename') %}
            <p>Selected file: <strong>{{ session['assignment_filename'] }}</strong></p>
          {% endif %}
          <br><br>
          
          <label>📜 Upload Assessment Brief (Max 5MB):</label><br>
          <input type="file" name="assessment_brief_file" accept=".pdf,.docx,.pptx" required>
          {% if session.get('assessment_brief_filename') %}
            <p>Selected file: <strong>{{ session['assessment_brief_filename'] }}</strong></p>
          {% endif %}
          <br><br>
          
          <label>📚 Upload Module Materials:</label><br>
          <input type="file" name="module_material_files" accept=".pdf,.docx,.pptx" multiple required>
          {% if session.get('module_material_filenames') %}
            <ul>
              {% for filename in session['module_material_filenames'] %}
                <li><strong>{{ filename }}</strong></li>
              {% endfor %}
            </ul>
          {% endif %}
          <br><br>
          
          <button type="submit" class="button">✅ Process Files</button>
        </form>
        
        {% if session.get('files_processed') %}
          <h3>Uploaded Files:</h3>
          <ul class="file-list">
            <li><strong>Assignment:</strong> {{ session['assignment_filename'] }}</li>
            <li><strong>Assessment Brief:</strong> {{ session['assessment_brief_filename'] }}</li>
            <li><strong>Module Materials:</strong>
              <ul>
                {% for filename in session['module_material_filenames'] %}
                  <li>{{ filename }}</li>
                {% endfor %}
              </ul>
            </li>
          </ul>
        {% endif %}
      </div>
      
      {% if session.get('files_processed') %}
      <div class="section">
        <h2>🛠️ Select Analysis Tools</h2>
        <form method="POST" action="{{ url_for('analyze_tools') }}">
          <h3>Select the tools you want to use:</h3>
          <input type="checkbox" name="compliance_check" id="compliance_check" onchange="toggleComplianceOptions()">
          <label for="compliance_check">Compliance Check</label><br>
          
          <div id="compliance_options" class="checkbox-group" style="display:none;">
            <input type="checkbox" name="assessment_brief_compliance" id="assessment_brief_compliance">
            <label for="assessment_brief_compliance">Assessment Brief Compliance</label><br>
            
            <input type="checkbox" name="module_materials_compliance" id="module_materials_compliance">
            <label for="module_materials_compliance">Module Materials Compliance</label><br>
          </div>
          
          <input type="checkbox" name="grammar_check" id="grammar_check">
          <label for="grammar_check">Grammar Check</label><br>
          
          <input type="checkbox" name="critical_writing_check" id="critical_writing_check">
          <label for="critical_writing_check">Critical Writing Check</label><br>
          
          <input type="checkbox" name="reference_check" id="reference_check" onclick="toggleReferenceStyle()">
          <label for="reference_check">Reference Check</label><br><br>
          
          <div id="reference_style_div" style="display:none;">
            <label for="reference_style">Select the Reference Style:</label><br>
            <select name="reference_style" id="reference_style">
              <option value="APA">APA</option>
              <option value="Harvard">Harvard</option>
              <option value="IEEE">IEEE</option>
              <option value="Chicago">Chicago</option>
              <option value="MLA">MLA</option>
            </select><br><br>
          </div>
          
          <button type="submit" class="button">🔍 Analyze Selected Tools</button>
        </form>
      </div>
      {% endif %}
      
      {% if session.get('analysis_completed') %}
      <div class="section">
        <h2>📥 Download Reports</h2>
        <p>You can view and download your generated reports on the <a href="{{ url_for('reports') }}">Reports</a> page.</p>
      </div>
      {% endif %}
      
    </div>
    
    <script>
      function toggleReferenceStyle() {
        var checkBox = document.getElementById("reference_check");
        var text = document.getElementById("reference_style_div");
        if (checkBox.checked == true){
          text.style.display = "block";
        } else {
          text.style.display = "none";
        }
      }
      
      function toggleComplianceOptions() {
        var checkBox = document.getElementById("compliance_check");
        var options = document.getElementById("compliance_options");
        if (checkBox.checked == true){
          options.style.display = "block";
        } else {
          options.style.display = "none";
        }
      }
    </script>
  </body>
</html>
"""

tutorial_template = """
<!doctype html>
<html lang="en">
  <head>
    <title>Tutorial - Academic QA Assistant 📚</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 40px; }
      .container { max-width: 800px; margin: auto; }
      a { text-decoration: none; color: #007bff; }
      a:hover { text-decoration: underline; }
    </style>
  </head>
  <body>
    """ + base_header + """
    <div class="container">
      <h1>Tutorial 📖</h1>
      <hr>
      <h2>Getting Started</h2>
      <p>Welcome to the Academic QA Assistant! This tutorial will guide you through the steps to effectively use the application.</p>
      
      <h3>Step 1: Upload Your Documents</h3>
      <p>Begin by uploading the necessary documents:</p>
      <ul>
        <li><strong>Student's Assignment:</strong> Upload the assignment file you want to analyze.</li>
        <li><strong>Assessment Brief:</strong> Upload the assessment brief to check compliance.</li>
        <li><strong>Module Materials:</strong> Upload all relevant module materials.</li>
      </ul>
      
      <h3>Step 2: Process Files</h3>
      <p>After uploading, click "Process Files" to extract and store the content for analysis.</p>
      
      <h3>Step 3: Select Analysis Tools</h3>
      <p>Choose the analysis tools you want to apply to your assignment:</p>
      <ul>
        <li><strong>Compliance Check:</strong> Ensure the assignment adheres to the assessment brief and module materials.</li>
        <li><strong>Grammar Check:</strong> Analyze grammar and language usage.</li>
        <li><strong>Critical Writing Check:</strong> Evaluate the critical thinking and writing quality.</li>
        <li><strong>Reference Check:</strong> Verify the references against the selected style (e.g., APA, Harvard).</li>
      </ul>
      
      <h3>Step 4: Analyze and Download Reports</h3>
      <p>After selecting the tools, click "Analyze Selected Tools" to perform the analysis. Once completed, you can view and download the reports on the Reports page.</p>
      
      <h2>Additional Tips</h2>
      <ul>
        <li>Ensure all uploaded files are within the size limits (Max 5MB each).</li>
        <li>Use consistent reference styles across all documents.</li>
        <li>Review the reports thoroughly to understand the feedback.</li>
      </ul>
      
      <p>For more assistance, feel free to reach out to our support team.</p>
    </div>
  </body>
</html>
"""

reports_template = """
<!doctype html>
<html lang="en">
  <head>
    <title>Reports - Academic QA Assistant 📚</title>
    <style>
      body {
        font-family: Arial, sans-serif; 
        margin: 40px;
      }
      .container {
        max-width: 800px; 
        margin: auto;
      }
      .section {
        margin-bottom: 30px;
      }
      .button {
        padding: 10px 20px; 
        background-color: green; 
        color: white; 
        border: none; 
        cursor: pointer;
        margin-bottom: 10px;
      }
      .button:hover {
        background-color: darkgreen;
      }
      a {
        text-decoration: none; 
        color: #007bff;
      }
      a:hover {
        text-decoration: underline;
      }
      .file-list {
        list-style-type: none; 
        padding: 0;
      }
      .file-list li {
        margin-bottom: 5px;
      }
      .choice-title {
        font-weight: bold;
        margin-bottom: 10px;
      }
      .report-section {
        border: 1px solid #ddd; 
        padding: 15px; 
        margin-bottom: 20px; 
        border-radius: 5px;
      }
      .report-section h3 {
        margin-top: 0;
      }
      .report-link {
        display: block; 
        margin-bottom: 8px; 
        color: #000;
      }
      .report-link:hover {
        text-decoration: underline;
      }
      .no-reports {
        color: #666;
        font-style: italic;
      }
    </style>
  </head>
  <body>
    """ + base_header + """
    <div class="container">
      <h1>📥 Download Reports</h1>
      <p>Below are your reports based on the tools you selected:</p>
      
      {% if analysis_completed %}
        {% set selected_tools = selected_tools %}
        
        {% set compliance_selected = selected_tools.get('compliance_checks', []) %}
        {% set grammar_selected = selected_tools.get('grammar_check', False) %}
        {% set critical_selected = selected_tools.get('critical_writing_check', False) %}
        {% set reference_selected = selected_tools.get('reference_check', False) %}
        
        {% set assignments = assignments %}
        
        {% if assignments %}
          {% for assignment in assignments %}
            <div class="report-section">
              <h3>Assignment: {{ assignment }}</h3>
              
              {% set have_reports = False %}
              
              {% if compliance_selected %}
                {% set compliance_reports = compliance_reports.get(assignment, {}) %}
                {% if compliance_reports %}
                  <h4>Compliance Reports</h4>
                  {% for report_title, pdf_filename in compliance_reports.items() %}
                    <a class="report-link" href="{{ url_for('view_report', assignment=assignment, report=report_title.replace(' ', '_')) }}" target="_blank">
                      View {{ report_title }}
                    </a>
                    {% set have_reports = True %}
                  {% endfor %}
                {% endif %}
              {% endif %}
              
              {% if grammar_selected %}
                {% set grammar_report = grammar_reports.get(assignment, None) %}
                {% if grammar_report %}
                  <h4>Grammar Check</h4>
                  <a class="report-link" href="{{ url_for('view_report', assignment=assignment, report='Grammar_Check') }}" target="_blank">
                    View Grammar Check
                  </a>
                  {% set have_reports = True %}
                {% endif %}
              {% endif %}
              
              {% if critical_selected %}
                {% set critical_report = critical_writing_reports.get(assignment, None) %}
                {% if critical_report %}
                  <h4>Critical Writing Check</h4>
                  <a class="report-link" href="{{ url_for('view_report', assignment=assignment, report='Critical_Writing_Check') }}" target="_blank">
                    View Critical Writing Check
                  </a>
                  {% set have_reports = True %}
                {% endif %}
              {% endif %}
              
              {% if reference_selected %}
                {% set reference_report = reference_reports.get(assignment, None) %}
                {% if reference_report %}
                  <h4>Reference Check</h4>
                  <a class="report-link" href="{{ url_for('view_report', assignment=assignment, report='Reference_Check') }}" target="_blank">
                    View Reference Check
                  </a>
                  {% set have_reports = True %}
                {% endif %}
              {% endif %}
              
              {% if not have_reports %}
                <p class="no-reports">No reports available for this assignment.</p>
              {% endif %}
            </div>
          {% endfor %}
          
          <h2>Download Your Reports</h2>
          <p>Select one or more download options to receive your reports as ZIP files.</p>
          <form method="POST" action="{{ url_for('download_reports') }}">
            {% if compliance_selected %}
              <button type="submit" name="download_tool" value="compliance" class="button">
                Download Compliance Reports
              </button><br>
            {% endif %}
            
            {% if grammar_selected %}
              <button type="submit" name="download_tool" value="grammar" class="button">
                Download Grammar Reports
              </button><br>
            {% endif %}
            
            {% if critical_selected %}
              <button type="submit" name="download_tool" value="critical_writing" class="button">
                Download Critical Writing Reports
              </button><br>
            {% endif %}
            
            {% if reference_selected %}
              <button type="submit" name="download_tool" value="reference" class="button">
                Download Reference Reports
              </button><br>
            {% endif %}
            
            {% if (compliance_selected or grammar_selected or critical_selected or reference_selected) %}
              <button type="submit" name="download_tool" value="all" class="button" style="background-color: #007bff;">
                Download All Reports
              </button>
            {% endif %}
          </form>
        {% else %}
          <p class="no-reports">No assignments found to generate reports for.</p>
        {% endif %}
      
      {% else %}
        <p class="no-reports">No reports have been generated yet. Please <a href="{{ url_for('home') }}">go back</a> and run the analysis first.</p>
      {% endif %}
      
    </div>
  </body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return render_template_string(home_template)

@app.route('/tutorial', methods=['GET'])
def tutorial():
    return render_template_string(tutorial_template)

@app.route('/reports', methods=['GET'])
def reports():
    # Fetch necessary data from session
    analysis_completed = session.get('analysis_completed', False)
    selected_tools = session.get('selected_tools', {})
    compliance_reports = session.get('compliance_reports', {})
    grammar_reports = session.get('grammar_reports', {})
    critical_writing_reports = session.get('critical_writing_reports', {})
    reference_reports = session.get('reference_reports', {})
    assignments = session.get('assignments_text', {}).keys()
    
    return render_template_string(reports_template,
                                  analysis_completed=analysis_completed,
                                  selected_tools=selected_tools,
                                  compliance_reports=compliance_reports,
                                  grammar_reports=grammar_reports,
                                  critical_writing_reports=critical_writing_reports,
                                  reference_reports=reference_reports,
                                  assignments=assignments)

@app.route('/process_files', methods=['POST'])
def process_files():
    try:
        assignment_file = request.files.get('assignment_file')
        assessment_brief_file = request.files.get('assessment_brief_file')
        module_material_files = request.files.getlist('module_material_files')
        
        # Validate files
        missing_files = []
        if not assignment_file or assignment_file.filename == '':
            missing_files.append("Student's Assignment")
        if not assessment_brief_file or assessment_brief_file.filename == '':
            missing_files.append("Assessment Brief")
        if not module_material_files or len(module_material_files) == 0 or all(f.filename == '' for f in module_material_files):
            missing_files.append("Module Materials")
        
        if missing_files:
            missing_str = ", ".join(missing_files)
            flash(f"🛑 The following required files are missing: {missing_str}. Please upload them.", "error")
            return redirect(url_for('home'))
        
        # Check file sizes (Max 5MB each)
        max_size = 5 * 1024 * 1024  # 5MB
        oversized_files = []
        for file in [assignment_file, assessment_brief_file] + module_material_files:
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            file.seek(0)
            if file_length > max_size:
                oversized_files.append(file.filename)
        
        if oversized_files:
            oversized_str = ", ".join(oversized_files)
            flash(f"🛑 The following files exceed the 5MB limit: {oversized_str}. Please upload smaller files.", "error")
            return redirect(url_for('home'))
        
        # Generate a new user ID for each file upload to prevent conflicts
        user_id = os.urandom(8).hex()
        session['user_id'] = user_id
        upload_folder = os.path.join('uploads', secure_filename(user_id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create a reports directory
        reports_folder = os.path.join(upload_folder, 'reports')
        os.makedirs(reports_folder, exist_ok=True)
        
        # Save files
        assignment_filename = secure_filename(assignment_file.filename)
        assignment_path = os.path.join(upload_folder, assignment_filename)
        assignment_file.save(assignment_path)
        session['assignment_filename'] = assignment_filename
        
        assessment_brief_filename = secure_filename(assessment_brief_file.filename)
        assessment_brief_path = os.path.join(upload_folder, assessment_brief_filename)
        assessment_brief_file.save(assessment_brief_path)
        session['assessment_brief_filename'] = assessment_brief_filename
        
        module_material_paths = []
        module_material_filenames = []
        for file in module_material_files:
            filename = secure_filename(file.filename)
            path = os.path.join(upload_folder, filename)
            file.save(path)
            module_material_paths.append(path)
            module_material_filenames.append(filename)
        session['module_material_filenames'] = module_material_filenames
        
        # Clear previous reports data if any
        session.pop('compliance_reports', None)
        session.pop('grammar_reports', None)
        session.pop('reference_reports', None)
        session.pop('critical_writing_reports', None)
        session.pop('analysis_completed', None)
        session.pop('selected_tools', None)
        
        # Remove any existing reports directory and recreate it
        if os.path.exists(reports_folder):
            shutil.rmtree(reports_folder)
        os.makedirs(reports_folder, exist_ok=True)
        
        # Process files
        files_dict = {
            "assignments": {assignment_filename: assignment_path},
            "assessment_briefs": {assessment_brief_filename: assessment_brief_path},
            "module_materials": {os.path.basename(path): path for path in module_material_paths}
        }
        assignments_text = extract_all_text(files_dict["assignments"])
        assessment_briefs_text = extract_all_text(files_dict["assessment_briefs"])
        module_materials_text = extract_all_text(files_dict["module_materials"])
        
        session['assignments_text'] = assignments_text
        session['assessment_briefs_text'] = assessment_briefs_text
        session['module_materials_text'] = module_materials_text
        session['files_processed'] = True
        
        flash("✅ Files processed and stored successfully!", "success")
        return redirect(url_for('home'))
    
    except Exception as e:
        logger.error(f"Error in process_files: {e}")
        flash(f"🛑 An error occurred while processing files: {e}", "error")
        return redirect(url_for('home'))

@app.route('/analyze_tools', methods=['POST'])
def analyze_tools():
    try:
        compliance_check = 'compliance_check' in request.form
        assessment_brief_compliance = 'assessment_brief_compliance' in request.form
        module_materials_compliance = 'module_materials_compliance' in request.form
        grammar_check_option = 'grammar_check' in request.form
        critical_writing_check_option = 'critical_writing_check' in request.form
        reference_check_option = 'reference_check' in request.form
        reference_style = request.form.get('reference_style') if reference_check_option else None
        
        selected_compliance_checks = []
        if compliance_check:
            if assessment_brief_compliance:
                selected_compliance_checks.append('assessment_brief')
            if module_materials_compliance:
                selected_compliance_checks.append('module_materials')
            if not selected_compliance_checks:
                flash("🛑 Please select at least one compliance check option.", "error")
                return redirect(url_for('home'))
        
        if not any([compliance_check, grammar_check_option, critical_writing_check_option, reference_check_option]):
            flash("🛑 Please select at least one tool to analyze.", "error")
            return redirect(url_for('home'))
        
        selected_tools = {
            'compliance_checks': selected_compliance_checks,
            'grammar_check': grammar_check_option,
            'critical_writing_check': critical_writing_check_option,
            'reference_check': reference_check_option,
            'reference_style': reference_style
        }
        
        session['selected_tools'] = selected_tools
        
        assignments_text = session.get('assignments_text', {})
        assessment_briefs_text = session.get('assessment_briefs_text', {})
        module_materials_text = session.get('module_materials_text', {})
        
        # Ensure user_id and reports_folder are available
        user_id = session.get('user_id')
        if not user_id:
            flash("🛑 Session expired or invalid. Please upload the files again.", "error")
            return redirect(url_for('home'))
        
        upload_folder = os.path.join('uploads', secure_filename(user_id))
        reports_folder = os.path.join(upload_folder, 'reports')
        os.makedirs(reports_folder, exist_ok=True)
        
        # Clear previous reports data before generating new reports
        session.pop('compliance_reports', None)
        session.pop('grammar_reports', None)
        session.pop('reference_reports', None)
        session.pop('critical_writing_reports', None)
        
        compliance_reports = {}
        grammar_reports = {}
        reference_reports = {}
        critical_writing_reports = {}
        
        total = len(assignments_text)
        if total == 0:
            flash("🛑 No assignments found for analysis.", "error")
            return redirect(url_for('home'))
        
        for assignment_name, assignment_text in assignments_text.items():
            compliance_reports[assignment_name] = {}
        
            if selected_tools['compliance_checks']:
                if 'assessment_brief' in selected_tools['compliance_checks']:
                    try:
                        # Assuming the first assessment brief corresponds to the assignment
                        assessment_brief_text = next(iter(assessment_briefs_text.values()))
                        response = check_assessment_compliance(groq_client, assignment_text, assessment_brief_text)
                        compliance_reports[assignment_name]['Assessment Brief Compliance'] = response
                        
                        # Save compliance report as a file
                        report_content = response
                        report_title = "Assessment Brief Compliance"
                        pdf_bytes = generate_individual_pdf_report(report_title, report_content)
                        pdf_filename = f"{assignment_name}_Assessment_Brief_Compliance.pdf"
                        pdf_path = os.path.join(reports_folder, pdf_filename)
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_bytes)
                        
                        compliance_reports[assignment_name][report_title] = pdf_filename
                        
                    except Exception as e:
                        error_message = f"🛑 Error: {e}"
                        compliance_reports[assignment_name]['Assessment Brief Compliance'] = error_message
                        logger.error(f"Error in Assessment Brief Compliance for {assignment_name}: {e}")
        
                if 'module_materials' in selected_tools['compliance_checks']:
                    try:
                        # Combine all module materials texts for compliance check
                        combined_module_text = "\n".join(module_materials_text.values())
                        response = check_module_compliance(groq_client, assignment_text, combined_module_text)
                        compliance_reports[assignment_name]['Module Materials Compliance'] = response
                        
                        # Save compliance report as a file
                        report_content = response
                        report_title = "Module Materials Compliance"
                        pdf_bytes = generate_individual_pdf_report(report_title, report_content)
                        pdf_filename = f"{assignment_name}_Module_Materials_Compliance.pdf"
                        pdf_path = os.path.join(reports_folder, pdf_filename)
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_bytes)
                        
                        compliance_reports[assignment_name][report_title] = pdf_filename
                        
                    except Exception as e:
                        error_message = f"🛑 Error: {e}"
                        compliance_reports[assignment_name]['Module Materials Compliance'] = error_message
                        logger.error(f"Error in Module Materials Compliance for {assignment_name}: {e}")
        
            if selected_tools['grammar_check']:
                try:
                    response = grammar_check(groq_client, assignment_text)
                    grammar_reports[assignment_name] = response
                    
                    # Save grammar report as a file
                    report_title = "Grammar_Check"
                    pdf_bytes = generate_individual_pdf_report(report_title, response)
                    pdf_filename = f"{assignment_name}_Grammar_Check.pdf"
                    pdf_path = os.path.join(reports_folder, pdf_filename)
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_bytes)
                    
                    grammar_reports[assignment_name] = pdf_filename
                    
                except Exception as e:
                    error_message = f"🛑 Error: {e}"
                    grammar_reports[assignment_name] = error_message
                    logger.error(f"Error in Grammar Check for {assignment_name}: {e}")
        
            if selected_tools['critical_writing_check']:
                try:
                    response = critical_writing_check(groq_client, assignment_text)
                    critical_writing_reports[assignment_name] = response
                    
                    # Save critical writing report as a file
                    report_title = "Critical_Writing_Check"
                    pdf_bytes = generate_individual_pdf_report(report_title, response)
                    pdf_filename = f"{assignment_name}_Critical_Writing_Check.pdf"
                    pdf_path = os.path.join(reports_folder, pdf_filename)
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_bytes)
                    
                    critical_writing_reports[assignment_name] = pdf_filename
                    
                except Exception as e:
                    error_message = f"🛑 Error: {e}"
                    critical_writing_reports[assignment_name] = error_message
                    logger.error(f"Error in Critical Writing Check for {assignment_name}: {e}")
        
            if selected_tools['reference_check']:
                if not selected_tools['reference_style']:
                    reference_reports[assignment_name] = "🛑 No reference style provided."
                    logger.warning(f"No reference style provided for Reference Check in {assignment_name}.")
                else:
                    try:
                        # Combine all module materials texts for reference check
                        combined_module_text = "\n".join(module_materials_text.values())
                        response = reference_check(
                            groq_client,
                            assignment_text,
                            combined_module_text,
                            reference_style=selected_tools['reference_style']
                        )
                        reference_reports[assignment_name] = response
                        
                        # Save reference report as a file
                        report_title = "Reference_Check"
                        pdf_bytes = generate_individual_pdf_report(report_title, response)
                        pdf_filename = f"{assignment_name}_Reference_Check.pdf"
                        pdf_path = os.path.join(reports_folder, pdf_filename)
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_bytes)
                        
                        reference_reports[assignment_name] = pdf_filename
                        
                    except Exception as e:
                        error_message = f"🛑 Error: {e}"
                        reference_reports[assignment_name] = error_message
                        logger.error(f"Error in Reference Check for {assignment_name}: {e}")
        
        # Update session with generated report filenames
        session['compliance_reports'] = compliance_reports
        session['grammar_reports'] = grammar_reports
        session['reference_reports'] = reference_reports
        session['critical_writing_reports'] = critical_writing_reports
        session['analysis_completed'] = True
        
        flash("✅ Analysis completed and reports generated!", "success")
        return redirect(url_for('reports'))
    
    except Exception as e:
        logger.error(f"Error in analyze_tools: {e}")
        flash(f"🛑 An error occurred during analysis: {e}", "error")
        return redirect(url_for('home'))

@app.route('/download_reports', methods=['POST'])
def download_reports():
    try:
        download_tool = request.values.get('download_tool')
        
        if not download_tool:
            flash("🛑 No download tool specified.", "error")
            return redirect(url_for('reports'))
        
        assignments = session.get('assignments_text', {})
        user_id = session.get('user_id')
        if not user_id:
            flash("🛑 Session expired or invalid. Please upload the files again.", "error")
            return redirect(url_for('home'))
        
        upload_folder = os.path.join('uploads', secure_filename(user_id))
        reports_folder = os.path.join(upload_folder, 'reports')
        
        if not os.path.exists(reports_folder):
            flash("🛑 Reports folder does not exist.", "error")
            return redirect(url_for('reports'))
        
        if not assignments:
            flash("🛑 No reports available for download.", "error")
            return redirect(url_for('reports'))
        
        # Initialize a buffer for the ZIP file
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_file:
            if download_tool == 'all':
                for assignment_name in assignments.keys():
                    # Compliance Reports
                    compliance_reports = session.get('compliance_reports', {}).get(assignment_name, {})
                    for report_title, pdf_filename in compliance_reports.items():
                        if isinstance(pdf_filename, str) and pdf_filename.endswith('.pdf'):
                            pdf_path = os.path.join(reports_folder, pdf_filename)
                            if os.path.exists(pdf_path):
                                # Organize inside assignment folders
                                zip_file.write(pdf_path, arcname=f"{assignment_name}/Compliance/{pdf_filename}")
                            else:
                                flash(f"🛑 Compliance report file not found: {pdf_filename}", "error")
                                logger.error(f"Compliance report file not found: {pdf_filename}")
                    
                    # Grammar Reports
                    grammar_report = session.get('grammar_reports', {}).get(assignment_name, None)
                    if isinstance(grammar_report, str) and grammar_report.endswith('.pdf'):
                        pdf_path = os.path.join(reports_folder, grammar_report)
                        if os.path.exists(pdf_path):
                            zip_file.write(pdf_path, arcname=f"{assignment_name}/Grammar/{grammar_report}")
                        else:
                            flash(f"🛑 Grammar report file not found: {grammar_report}", "error")
                            logger.error(f"Grammar report file not found: {grammar_report}")
                    
                    # Critical Writing Reports
                    critical_report = session.get('critical_writing_reports', {}).get(assignment_name, None)
                    if isinstance(critical_report, str) and critical_report.endswith('.pdf'):
                        pdf_path = os.path.join(reports_folder, critical_report)
                        if os.path.exists(pdf_path):
                            zip_file.write(pdf_path, arcname=f"{assignment_name}/Critical_Writing/{critical_report}")
                        else:
                            flash(f"🛑 Critical Writing report file not found: {critical_report}", "error")
                            logger.error(f"Critical Writing report file not found: {critical_report}")
                    
                    # Reference Reports
                    reference_report = session.get('reference_reports', {}).get(assignment_name, None)
                    if isinstance(reference_report, str) and reference_report.endswith('.pdf'):
                        pdf_path = os.path.join(reports_folder, reference_report)
                        if os.path.exists(pdf_path):
                            zip_file.write(pdf_path, arcname=f"{assignment_name}/Reference/{reference_report}")
                        else:
                            flash(f"🛑 Reference report file not found: {reference_report}", "error")
                            logger.error(f"Reference report file not found: {reference_report}")
            
            else:
                for assignment_name in assignments.keys():
                    if download_tool == 'compliance':
                        compliance_reports = session.get('compliance_reports', {}).get(assignment_name, {})
                        for report_title, pdf_filename in compliance_reports.items():
                            if isinstance(pdf_filename, str) and pdf_filename.endswith('.pdf'):
                                pdf_path = os.path.join(reports_folder, pdf_filename)
                                if os.path.exists(pdf_path):
                                    zip_file.write(pdf_path, arcname=pdf_filename)
                                else:
                                    flash(f"🛑 Compliance report file not found: {pdf_filename}", "error")
                                    logger.error(f"Compliance report file not found: {pdf_filename}")
                    
                    elif download_tool == 'grammar':
                        grammar_report = session.get('grammar_reports', {}).get(assignment_name, None)
                        if isinstance(grammar_report, str) and grammar_report.endswith('.pdf'):
                            pdf_path = os.path.join(reports_folder, grammar_report)
                            if os.path.exists(pdf_path):
                                zip_file.write(pdf_path, arcname=grammar_report)
                            else:
                                flash(f"🛑 Grammar report file not found: {grammar_report}", "error")
                                logger.error(f"Grammar report file not found: {grammar_report}")
                    
                    elif download_tool == 'critical_writing':
                        critical_report = session.get('critical_writing_reports', {}).get(assignment_name, None)
                        if isinstance(critical_report, str) and critical_report.endswith('.pdf'):
                            pdf_path = os.path.join(reports_folder, critical_report)
                            if os.path.exists(pdf_path):
                                zip_file.write(pdf_path, arcname=critical_report)
                            else:
                                flash(f"🛑 Critical Writing report file not found: {critical_report}", "error")
                                logger.error(f"Critical Writing report file not found: {critical_report}")
                    
                    elif download_tool == 'reference':
                        reference_report = session.get('reference_reports', {}).get(assignment_name, None)
                        if isinstance(reference_report, str) and reference_report.endswith('.pdf'):
                            pdf_path = os.path.join(reports_folder, reference_report)
                            if os.path.exists(pdf_path):
                                zip_file.write(pdf_path, arcname=reference_report)
                            else:
                                flash(f"🛑 Reference report file not found: {reference_report}", "error")
                                logger.error(f"Reference report file not found: {reference_report}")
                    else:
                        flash("🛑 Invalid download option selected.", "error")
                        logger.warning(f"Invalid download option selected: {download_tool}")
        
        if download_tool != 'all' and zip_buffer.tell() == 0:
            flash("🛑 No reports available for the selected tool.", "error")
            return redirect(url_for('reports'))
        
        if download_tool == 'all' and zip_buffer.tell() == 0:
            flash("🛑 No reports available to compile.", "error")
            return redirect(url_for('reports'))
        
        zip_buffer.seek(0)
        
        if download_tool == 'all':
            filename = 'All_Reports.zip'
        else:
            filename = f'{download_tool.capitalize()}_Reports.zip'
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error in download_reports: {e}")
        flash(f"🛑 An error occurred while generating reports: {e}", "error")
        return redirect(url_for('reports'))

@app.route('/view_report')
def view_report():
    try:
        assignment = request.args.get('assignment')
        report = request.args.get('report')
        
        if not assignment or not report:
            flash("🛑 Invalid report parameters.", "error")
            return redirect(url_for('reports'))
        
        user_id = session.get('user_id')
        if not user_id:
            flash("🛑 Session expired or invalid. Please upload the files again.", "error")
            return redirect(url_for('home'))
        
        upload_folder = os.path.join('uploads', secure_filename(user_id))
        reports_folder = os.path.join(upload_folder, 'reports')
        
        # Determine the report filename based on the report type
        if "Compliance" in report:
            report_filename = f"{assignment}_{report}.pdf"
        elif report in ['Grammar_Check', 'Critical_Writing_Check', 'Reference_Check']:
            report_filename = f"{assignment}_{report}.pdf"
        else:
            flash("🛑 Invalid Report Type.", "error")
            logger.warning(f"Invalid report type requested: {report} for assignment: {assignment}")
            return redirect(url_for('reports'))
        
        pdf_path = os.path.join(reports_folder, report_filename)
        if not os.path.exists(pdf_path):
            flash(f"🛑 Report file not found: {report_filename}", "error")
            logger.error(f"Report file not found: {pdf_path}")
            return redirect(url_for('reports'))
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=report_filename
        )
    
    except Exception as e:
        logger.error(f"Error in view_report: {e}")
        flash(f"🛑 An error occurred while viewing the report: {e}", "error")
        return redirect(url_for('reports'))

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("🛑 File too large. Maximum upload size is 16MB.", "error")
    return redirect(url_for('home'))

if __name__ == "__main__":
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=8000)














# --------------  previous code ---------------------------------

# from flask import Flask, render_template_string, request, redirect, url_for, send_file, session, flash
# from werkzeug.utils import secure_filename
# from dotenv import load_dotenv
# import os
# import io

# # Import custom modules
# from utils.groq_integration import GroqClient
# from utils.file_processing import extract_all_text
# from utils.pdf_generation_reportlab import generate_individual_pdf_report, generate_compiled_pdf_report
# from tools.compliance_checks import check_assessment_compliance, check_module_compliance
# from tools.grammar_check import grammar_check
# from tools.reference_check import reference_check
# from tools.critical_writing_check import critical_writing_check

# # Load environment variables from a .env file
# load_dotenv()

# # Initialize Flask app
# app = Flask(__name__)
# app.secret_key = os.urandom(24)  # Ensure you set a secure secret key in production
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

# # Initialize GroqClient
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise EnvironmentError("🛑 GROQ_API_KEY not found. Please set it in the environment variables.")
# groq_client = GroqClient(api_key=GROQ_API_KEY)

# # HTML Templates as strings
# base_header = """
# <header>
#     <nav style="background-color: #f8f9fa; padding: 10px;">
#         <a href="{{ url_for('home') }}" style="margin-right: 15px;">Home</a>
#         <a href="{{ url_for('tutorial') }}" style="margin-right: 15px;">Tutorial</a>
#         <a href="{{ url_for('reports') }}">Reports</a>
#     </nav>
# </header>
# <hr>
# """

# home_template = f"""
# <!doctype html>
# <html lang="en">
#   <head>
#     <title>Academic QA Assistant 📚</title>
#     <style>
#       body {{ font-family: Arial, sans-serif; margin: 40px; }}
#       .container {{ max-width: 800px; margin: auto; }}
#       .error {{ color: red; }}
#       .success {{ color: green; }}
#       .section {{ margin-bottom: 30px; }}
#       .button {{ padding: 10px 20px; background-color: green; color: white; border: none; cursor: pointer; }}
#       .button:hover {{ background-color: darkgreen; }}
#       a {{ text-decoration: none; color: #007bff; }}
#       a:hover {{ text-decoration: underline; }}
#     </style>
#   </head>
#   <body>
#     {base_header}
#     <div class="container">
#       <h1>Academic QA Assistant 📚</h1>
#       <h3>Automate Quality Assurance for Academic Assignments with AI 🧠</h3>
#       <hr>
      
#       {{% with messages = get_flashed_messages(with_categories=true) %}}
#         {{% if messages %}}
#           {{% for category, message in messages %}}
#             <p class="{{{{ category }}}}">{{{{ message }}}}</p>
#           {{% endfor %}}
#         {{% endif %}}
#       {{% endwith %}}
      
#       <div class="section">
#         <h2>📁 Upload Your Documents</h2>
#         <form method="POST" action="{{{{ url_for('process_files') }}}}" enctype="multipart/form-data">
#           <label>📄 Upload Student's Assignment (Max 5MB):</label><br>
#           <input type="file" name="assignment_file" accept=".pdf,.docx,.pptx" required><br><br>
          
#           <label>📜 Upload Assessment Brief (Max 5MB):</label><br>
#           <input type="file" name="assessment_brief_file" accept=".pdf,.docx,.pptx" required><br><br>
          
#           <label>📚 Upload Module Materials:</label><br>
#           <input type="file" name="module_material_files" accept=".pdf,.docx,.pptx" multiple required><br><br>
          
#           <button type="submit" class="button">✅ Process Files</button>
#         </form>
#       </div>
      
#       {{% if session.get('files_processed') %}}
#       <div class="section">
#         <h2>🛠️ Select Analysis Tools</h2>
#         <form method="POST" action="{{{{ url_for('analyze_tools') }}}}">
#           <h3>Select the tools you want to use:</h3>
#           <input type="checkbox" name="compliance_check" id="compliance_check">
#           <label for="compliance_check">Compliance Check</label><br>
          
#           <input type="checkbox" name="grammar_check" id="grammar_check">
#           <label for="grammar_check">Grammar Check</label><br>
          
#           <input type="checkbox" name="critical_writing_check" id="critical_writing_check">
#           <label for="critical_writing_check">Critical Writing Check</label><br>
          
#           <input type="checkbox" name="reference_check" id="reference_check" onclick="toggleReferenceStyle()">
#           <label for="reference_check">Reference Check</label><br><br>
          
#           <div id="reference_style_div" style="display:none;">
#             <label for="reference_style">Select the Reference Style:</label><br>
#             <select name="reference_style" id="reference_style">
#               <option value="APA">APA</option>
#               <option value="Harvard">Harvard</option>
#               <option value="IEEE">IEEE</option>
#               <option value="Chicago">Chicago</option>
#               <option value="MLA">MLA</option>
#             </select><br><br>
#           </div>
          
#           <button type="submit" class="button">🔍 Analyze Selected Tools</button>
#         </form>
#       </div>
#       {{% endif %}}
      
#       {{% if session.get('analysis_completed') %}}
#       <div class="section">
#         <h2>📥 Download Reports</h2>
#         <form method="POST" action="{{{{ url_for('download_reports') }}}}">
#           <h3>Choose your download option:</h3>
#           {{% if session.get('tools_used') > 1 %}}
#             <input type="radio" id="individual" name="download_choice" value="individual" checked>
#             <label for="individual">Individual Reports</label><br>
#             <input type="radio" id="compiled" name="download_choice" value="compiled">
#             <label for="compiled">Compiled Report</label><br><br>
#           {{% else %}}
#             <input type="radio" id="individual" name="download_choice" value="individual" checked disabled>
#             <label for="individual">Individual Reports</label><br><br>
#           {{% endif %}}
          
#           <button type="submit" class="button">🔽 Download Report</button>
#         </form>
#       </div>
#       {{% endif %}}
      
#     </div>
    
#     <script>
#       function toggleReferenceStyle() {{
#         var checkBox = document.getElementById("reference_check");
#         var text = document.getElementById("reference_style_div");
#         if (checkBox.checked == true){{
#           text.style.display = "block";
#         }} else {{
#           text.style.display = "none";
#         }}
#       }}
#     </script>
#   </body>
# </html>
# """

# tutorial_template = f"""
# <!doctype html>
# <html lang="en">
#   <head>
#     <title>Tutorial - Academic QA Assistant 📚</title>
#     <style>
#       body {{ font-family: Arial, sans-serif; margin: 40px; }}
#       .container {{ max-width: 800px; margin: auto; }}
#       a {{ text-decoration: none; color: #007bff; }}
#       a:hover {{ text-decoration: underline; }}
#     </style>
#   </head>
#   <body>
#     {base_header}
#     <div class="container">
#       <h1>Tutorial 📖</h1>
#       <hr>
#       <h2>Getting Started</h2>
#       <p>Welcome to the Academic QA Assistant! This tutorial will guide you through the steps to effectively use the application.</p>
      
#       <h3>Step 1: Upload Your Documents</h3>
#       <p>Begin by uploading the necessary documents:</p>
#       <ul>
#         <li><strong>Student's Assignment:</strong> Upload the assignment file you want to analyze.</li>
#         <li><strong>Assessment Brief:</strong> Upload the assessment brief to check compliance.</li>
#         <li><strong>Module Materials:</strong> Upload all relevant module materials.</li>
#       </ul>
      
#       <h3>Step 2: Process Files</h3>
#       <p>After uploading, click on "Process Files" to extract and store the content for analysis.</p>
      
#       <h3>Step 3: Select Analysis Tools</h3>
#       <p>Choose the analysis tools you want to apply to your assignment:</p>
#       <ul>
#         <li><strong>Compliance Check:</strong> Ensure the assignment adheres to the assessment brief and module materials.</li>
#         <li><strong>Grammar Check:</strong> Analyze the grammar and language usage.</li>
#         <li><strong>Critical Writing Check:</strong> Evaluate the critical thinking and writing quality.</li>
#         <li><strong>Reference Check:</strong> Verify the references against the selected style (e.g., APA, Harvard).</li>
#       </ul>
      
#       <h3>Step 4: Analyze and Download Reports</h3>
#       <p>After selecting the tools, click "Analyze Selected Tools" to perform the analysis. Once completed, you can download the reports in your preferred format.</p>
      
#       <h2>Additional Tips</h2>
#       <ul>
#         <li>Ensure all uploaded files are within the size limits (Max 5MB each).</li>
#         <li>Use consistent reference styles across all documents.</li>
#         <li>Review the reports thoroughly to understand the feedback.</li>
#       </ul>
      
#       <p>For more assistance, feel free to reach out to our support team.</p>
#     </div>
#   </body>
# </html>
# """

# reports_template = f"""
# <!doctype html>
# <html lang="en">
#   <head>
#     <title>Reports - Academic QA Assistant 📚</title>
#     <style>
#       body {{ font-family: Arial, sans-serif; margin: 40px; }}
#       .container {{ max-width: 800px; margin: auto; }}
#       table {{ width: 100%; border-collapse: collapse; }}
#       th, td {{ border: 1px solid #ddd; padding: 8px; }}
#       th {{ background-color: #f2f2f2; }}
#       a {{ text-decoration: none; color: #007bff; }}
#       a:hover {{ text-decoration: underline; }}
#       .button {{ padding: 10px 20px; border-radius: 5px; margin: 10px 5px;  background-color: green; color: white; border: none; cursor: pointer; text-decoration: none; }}
#       .button:hover {{ background-color: darkgreen; }}
#       .button:container {{ display: flex; gap: 50px; flex-wrap: wrap;  list-style: none; padding: 0; margin: 0 ;justify-content: center;    }}
#       .button-container {{ display: flex;gap: 50px;flex-wrap: wrap;list-style: none;padding: 0;margin: 0;justify-content: center;
# }}

#     </style>
#   </head>
#   <body>
#     {base_header}
#     <div class="container">
#       <h1>Reports 📑</h1>
#       <hr>
      
#       {{% if session.get('analysis_completed') %}}
#         <h2>Your Reports are Ready</h2>
#         <p>You have successfully generated reports. You can download them using the links below:</p>
#         <ul class ="button-container" list-style: none; margin: 0;padding: 0; >
#           <li margin-bottom: 30px;><a href="{{{{ url_for('download_reports') }}}}?download_choice=individual" class="button">Download Individual Reports</a></li>
#           <li margin-bottom: 30px;><a href="{{{{ url_for('download_reports') }}}}?download_choice=compiled" class="button">Download Compiled Report</a></li>
#         </ul>
#       {{% else %}}
#         <p>No reports available. Please <a href="{{{{ url_for('home') }}}}">go back to the home page</a> to generate reports.</p>
#       {{% endif %}}
#     </div>
#   </body>
# </html>
# """

# @app.route('/', methods=['GET'])
# def home():
#     return render_template_string(home_template)

# @app.route('/tutorial', methods=['GET'])
# def tutorial():
#     return render_template_string(tutorial_template)

# @app.route('/reports', methods=['GET'])
# def reports():
#     return render_template_string(reports_template)

# @app.route('/process_files', methods=['POST'])
# def process_files():
#     try:
#         # Retrieve uploaded files
#         assignment_file = request.files.get('assignment_file')
#         assessment_brief_file = request.files.get('assessment_brief_file')
#         module_material_files = request.files.getlist('module_material_files')
        
#         # Validate files
#         if not assignment_file or not assessment_brief_file or not module_material_files:
#             flash("🛑 Please upload all required files.", "error")
#             return redirect(url_for('home'))
        
#         # Check file sizes (Max 5MB each)
#         max_size = 5 * 1024 * 1024  # 5MB
#         for file in [assignment_file, assessment_brief_file] + module_material_files:
#             file.seek(0, os.SEEK_END)
#             file_length = file.tell()
#             file.seek(0)
#             if file_length > max_size:
#                 flash(f"🛑 File {file.filename} exceeds 5MB limit. Please upload a smaller file.", "error")
#                 return redirect(url_for('home'))
        
#         # Save files to a temporary directory
#         user_id = session.get('user_id', os.urandom(8).hex())
#         session['user_id'] = user_id  # Ensure user_id is stored in session
#         upload_folder = os.path.join('uploads', secure_filename(user_id))
#         os.makedirs(upload_folder, exist_ok=True)
        
#         assignment_path = os.path.join(upload_folder, secure_filename(assignment_file.filename))
#         assignment_file.save(assignment_path)
        
#         assessment_brief_path = os.path.join(upload_folder, secure_filename(assessment_brief_file.filename))
#         assessment_brief_file.save(assessment_brief_path)
        
#         module_material_paths = []
#         for file in module_material_files:
#             path = os.path.join(upload_folder, secure_filename(file.filename))
#             file.save(path)
#             module_material_paths.append(path)
        
#         # Process files
#         files_dict = {
#             "assignments": {assignment_file.filename: assignment_path},
#             "assessment_briefs": {assessment_brief_file.filename: assessment_brief_path},
#             "module_materials": {os.path.basename(path): path for path in module_material_paths}
#         }
#         assignments_text = extract_all_text(files_dict["assignments"])
#         assessment_briefs_text = extract_all_text(files_dict["assessment_briefs"])
#         module_materials_text = extract_all_text(files_dict["module_materials"])
        
#         # Store in session
#         session['assignments_text'] = assignments_text
#         session['assessment_briefs_text'] = assessment_briefs_text
#         session['module_materials_text'] = module_materials_text
#         session['files_processed'] = True
        
#         flash("✅ Files processed and stored successfully!", "success")
#         return redirect(url_for('home'))
    
#     except Exception as e:
#         flash(f"🛑 An error occurred while processing files: {e}", "error")
#         return redirect(url_for('home'))

# @app.route('/analyze_tools', methods=['POST'])
# def analyze_tools():
#     try:
#         # Retrieve selected tools
#         compliance_check = 'compliance_check' in request.form
#         grammar_check_option = 'grammar_check' in request.form
#         critical_writing_check_option = 'critical_writing_check' in request.form
#         reference_check_option = 'reference_check' in request.form
#         reference_style = request.form.get('reference_style') if reference_check_option else None
        
#         if not any([compliance_check, grammar_check_option, critical_writing_check_option, reference_check_option]):
#             flash("🛑 Please select at least one tool to analyze.", "error")
#             return redirect(url_for('home'))
        
#         selected_tools = {
#             'compliance_checks': [],
#             'grammar_check': grammar_check_option,
#             'critical_writing_check': critical_writing_check_option,
#             'reference_check': reference_check_option,
#             'reference_style': reference_style
#         }
        
#         if compliance_check:
#             # For simplicity, assume both compliance checks are selected
#             selected_tools['compliance_checks'] = ['assessment_brief', 'module_materials']
        
#         session['selected_tools'] = selected_tools
        
#         # Perform analysis
#         assignments_text = session.get('assignments_text', {})
#         assessment_briefs_text = session.get('assessment_briefs_text', {})
#         module_materials_text = session.get('module_materials_text', {})
        
#         compliance_reports = {}
#         grammar_reports = {}
#         reference_reports = {}
#         critical_writing_reports = {}
        
#         total = len(assignments_text)
#         if total == 0:
#             flash("🛑 No assignments found for analysis.", "error")
#             return redirect(url_for('home'))
        
#         for assignment_name, assignment_text in assignments_text.items():
#             # Initialize report dictionary for this assignment
#             compliance_reports[assignment_name] = {}
        
#             # Compliance Checks
#             if selected_tools['compliance_checks']:
#                 if 'assessment_brief' in selected_tools['compliance_checks']:
#                     try:
#                         # Assuming the first assessment brief corresponds to the assignment
#                         assessment_brief_text = next(iter(assessment_briefs_text.values()))
#                         response = check_assessment_compliance(
#                             groq_client,
#                             assignment_text,
#                             assessment_brief_text
#                         )
#                         compliance_reports[assignment_name]['Assessment Brief Compliance'] = response
#                     except Exception as e:
#                         compliance_reports[assignment_name]['Assessment Brief Compliance'] = f"🛑 Error: {e}"
        
#                 if 'module_materials' in selected_tools['compliance_checks']:
#                     try:
#                         # Assuming the first module material corresponds to the assignment
#                         module_material_text = next(iter(module_materials_text.values()))
#                         response = check_module_compliance(
#                             groq_client,
#                             assignment_text,
#                             module_material_text
#                         )
#                         compliance_reports[assignment_name]['Module Materials Compliance'] = response
#                     except Exception as e:
#                         compliance_reports[assignment_name]['Module Materials Compliance'] = f"🛑 Error: {e}"
        
#             # Grammar Check
#             if selected_tools['grammar_check']:
#                 try:
#                     response = grammar_check(groq_client, assignment_text)
#                     grammar_reports[assignment_name] = response
#                 except Exception as e:
#                     grammar_reports[assignment_name] = f"🛑 Error: {e}"
        
#             # Critical Writing Check
#             if selected_tools['critical_writing_check']:
#                 try:
#                     response = critical_writing_check(groq_client, assignment_text)
#                     critical_writing_reports[assignment_name] = response
#                 except Exception as e:
#                     critical_writing_reports[assignment_name] = f"🛑 Error: {e}"
        
#             # Reference Check
#             if selected_tools['reference_check']:
#                 if not reference_style:
#                     reference_reports[assignment_name] = "🛑 No reference style provided."
#                 else:
#                     try:
#                         # Assuming module materials contain necessary references
#                         module_material_text = next(iter(module_materials_text.values()))
#                         response = reference_check(
#                             groq_client,
#                             assignment_text,
#                             module_material_text,
#                             reference_style=reference_style
#                         )
#                         reference_reports[assignment_name] = response
#                     except Exception as e:
#                         reference_reports[assignment_name] = f"🛑 Error: {e}"
        
#         # Store reports in session
#         session['compliance_reports'] = compliance_reports
#         session['grammar_reports'] = grammar_reports
#         session['reference_reports'] = reference_reports
#         session['critical_writing_reports'] = critical_writing_reports
#         session['analysis_completed'] = True
#         session['tools_used'] = sum([
#             len(selected_tools['compliance_checks']),
#             int(selected_tools['grammar_check']),
#             int(selected_tools['critical_writing_check']),
#             int(selected_tools['reference_check'])
#         ])
        
#         flash("✅ Analysis completed and reports generated!", "success")
#         return redirect(url_for('home'))
    
#     except Exception as e:
#         flash(f"🛑 An error occurred during analysis: {e}", "error")
#         return redirect(url_for('home'))

# @app.route('/download_reports', methods=['POST', 'GET'])
# def download_reports():
#     try:
#         if request.method == 'POST':
#             download_choice = request.form.get('download_choice', 'individual')
#         else:
#             download_choice = request.args.get('download_choice', 'individual')
        
#         assignments_text = session.get('assignments_text', {})
        
#         if not assignments_text:
#             flash("🛑 No reports available for download.", "error")
#             return redirect(url_for('home'))
        
#         if download_choice == 'individual':
#             # Generate a ZIP file containing all individual reports
#             from zipfile import ZipFile
#             zip_buffer = io.BytesIO()
#             with ZipFile(zip_buffer, 'w') as zip_file:
#                 for assignment_name in assignments_text.keys():
#                     # Collect all available reports for the assignment
#                     available_reports = []
#                     compliance_reports = session.get('compliance_reports', {}).get(assignment_name, {})
#                     grammar_report = session.get('grammar_reports', {}).get(assignment_name, "")
#                     critical_writing_report = session.get('critical_writing_reports', {}).get(assignment_name, "")
#                     reference_report = session.get('reference_reports', {}).get(assignment_name, "")
                    
#                     if compliance_reports:
#                         for key, content in compliance_reports.items():
#                             available_reports.append((key, content))
#                     if grammar_report:
#                         available_reports.append(("Grammar Check", grammar_report))
#                     if critical_writing_report:
#                         available_reports.append(("Critical Writing Check", critical_writing_report))
#                     if reference_report:
#                         available_reports.append(("Reference Check", reference_report))
                    
#                     for report_title, report_content in available_reports:
#                         pdf_bytes = generate_individual_pdf_report(report_title, report_content)
#                         pdf_filename = f"{assignment_name}_{report_title.replace(' ', '_')}.pdf"
#                         zip_file.writestr(pdf_filename, pdf_bytes)
            
#             zip_buffer.seek(0)
#             return send_file(
#                 zip_buffer,
#                 mimetype='application/zip',
#                 as_attachment=True,
#                 download_name='Individual_Reports.zip'
#             )
        
#         elif download_choice == 'compiled':
#             # Generate a ZIP file containing all compiled reports
#             from zipfile import ZipFile
#             zip_buffer = io.BytesIO()
#             with ZipFile(zip_buffer, 'w') as zip_file:
#                 for assignment_name in assignments_text.keys():
#                     reports_dict = {}
#                     compliance_reports = session.get('compliance_reports', {}).get(assignment_name, {})
#                     for key, report_content in compliance_reports.items():
#                         reports_dict[key] = report_content
#                     grammar_report = session.get('grammar_reports', {}).get(assignment_name, "")
#                     if grammar_report:
#                         reports_dict['Grammar Check'] = grammar_report
#                     critical_writing_report = session.get('critical_writing_reports', {}).get(assignment_name, "")
#                     if critical_writing_report:
#                         reports_dict['Critical Writing Check'] = critical_writing_report
#                     reference_report = session.get('reference_reports', {}).get(assignment_name, "")
#                     if reference_report:
#                         reports_dict['Reference Check'] = reference_report
                    
#                     pdf_bytes = generate_compiled_pdf_report(assignment_name, reports_dict)
#                     pdf_filename = f"{assignment_name}_Compiled_QA_Report.pdf"
#                     zip_file.writestr(pdf_filename, pdf_bytes)
            
#             zip_buffer.seek(0)
#             return send_file(
#                 zip_buffer,
#                 mimetype='application/zip',
#                 as_attachment=True,
#                 download_name='Compiled_Reports.zip'
#             )
        
#         else:
#             flash("🛑 Invalid download option selected.", "error")
#             return redirect(url_for('home'))
    
#     except Exception as e:
#         flash(f"🛑 An error occurred while generating reports: {e}", "error")
#         return redirect(url_for('home'))

# if __name__ == "__main__":
#     app.run(debug=True , port=8000)
