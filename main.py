import streamlit as st
from dotenv import load_dotenv
import os

# Import custom modules
from utils.groq_integration import GroqClient
from utils.file_processing import extract_all_text
from utils.pdf_generation_reportlab import generate_individual_pdf_report, generate_compiled_pdf_report
from tools.compliance_checks import check_assessment_compliance, check_module_compliance
from tools.grammar_check import grammar_check
from tools.reference_check import reference_check
from tools.critical_writing_check import critical_writing_check

# Import option menu for top navigation
from streamlit_option_menu import option_menu

# Load environment variables from a .env file
load_dotenv()

# Initialize GroqClient
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("🛑 GROQ_API_KEY not found. Please set it in the environment variables.")
    st.stop()
groq_client = GroqClient(api_key=GROQ_API_KEY)

# Configure page layout
st.set_page_config(page_title="Academic QA Assistant", layout="wide")

# Top Navigation Bar
with st.container():
    selected = option_menu(
        menu_title=None,  # No title
        options=["Home", "Reports", "Tutorial"],
        icons=["house", "file-earmark-text", "book"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "25px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "green"},
        }
    )

def home():
    st.title("Academic QA Assistant 📚")
    st.subheader("Automate Quality Assurance for Academic Assignments with AI 🧠")
    st.write("---")
    
    # File Upload Section
    st.header("📁 Upload Your Documents")
    
    # Use columns for better layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
         assignment_file = st.file_uploader(
        "📄 Upload Student's Assignment (Max 5MB)",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=False,
        key="assignment"
    )
    # Check file size
    if assignment_file and assignment_file.size > 5 * 1024 * 1024:
        st.error("🛑 File size exceeds 5MB limit. Please upload a smaller file.")
        assignment_file = None
    
    with col2:
        assessment_brief_file = st.file_uploader(
        "📜 Upload Assessment Brief (Max 5MB)",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=False,
        key="assessment_brief"
    )
    # Check file size
    if assessment_brief_file and assessment_brief_file.size > 5 * 1024 * 1024:
        st.error("🛑 File size exceeds 5MB limit. Please upload a smaller file.")
        assessment_brief_file = None
    
    with col3:
        module_material_files = st.file_uploader(
        "📚 Upload Module Materials",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=True,
        key="module_materials"
    )
    
    if st.button("✅ Process Files"):
        try:
            if not assignment_file or not assessment_brief_file or not module_material_files:
                st.error("🛑 Please upload all required files.")
            else:
                # Process files
                with st.spinner("🔄 Processing files..."):
                    files_dict = {
                        "assignments": [assignment_file],
                        "assessment_briefs": [assessment_brief_file],
                        "module_materials": module_material_files
                    }
                    assignments_text = extract_all_text(files_dict["assignments"])
                    assessment_briefs_text = extract_all_text(files_dict["assessment_briefs"])
                    module_materials_text = extract_all_text(files_dict["module_materials"])
    
                st.session_state['assignments_text'] = assignments_text
                st.session_state['assessment_briefs_text'] = assessment_briefs_text
                st.session_state['module_materials_text'] = module_materials_text
    
                st.success("✅ Files processed and stored successfully!")
        except Exception as e:
            st.error(f"🛑 An error occurred while processing files: {e}")

    # Show Analysis Section only if files are processed
    if 'assignments_text' in st.session_state:
        st.write("---")
        st.header("🛠️ Select Analysis Tools")
    
        # Tool selection
        st.write("### Select the tools you want to use:")
        compliance_check = st.checkbox("Compliance Check")
        grammar_check_option = st.checkbox("Grammar Check")
        critical_writing_check_option = st.checkbox("Critical Writing Check")
        reference_check_option = st.checkbox("Reference Check")
    
        selected_compliance_checks = []
        if compliance_check:
            st.write("**Compliance Checks:**")
            assessment_brief_compliance = st.checkbox("Assessment Brief Compliance", key="assessment_brief_compliance")
            module_compliance = st.checkbox("Module Materials Compliance", key="module_compliance")
            if assessment_brief_compliance:
                selected_compliance_checks.append('assessment_brief')
            if module_compliance:
                selected_compliance_checks.append('module_materials')
    
        # Reference style input is deferred to download phase
        if reference_check_option:
            st.write("**Reference Style:**")
            reference_style = st.selectbox(
                "Select the Reference Style",
                ["APA", "Harvard", "IEEE", "Chicago", "MLA"],
                index=0,
                key="reference_style"
            )
        else:
            reference_style = None
    
        # Analyze button
        if st.button("🔍 Analyze Selected Tools"):
            if not any([compliance_check, grammar_check_option, critical_writing_check_option, reference_check_option]):
                st.error("🛑 Please select at least one tool to analyze.")
            else:
                # Store selected tools in session state
                st.session_state['selected_tools'] = {
                    'compliance_checks': selected_compliance_checks,
                    'grammar_check': grammar_check_option,
                    'critical_writing_check': critical_writing_check_option,
                    'reference_check': reference_check_option,
                    'reference_style': reference_style
                }
                # Proceed to analysis
                analyze_tools()

def analyze_tools():
    assignments_text = st.session_state['assignments_text']
    assessment_briefs_text = st.session_state['assessment_briefs_text']
    module_materials_text = st.session_state['module_materials_text']
    selected_tools = st.session_state['selected_tools']

    compliance_reports = {}
    grammar_reports = {}
    reference_reports = {}
    critical_writing_reports = {}

    total = len(assignments_text)
    progress = st.progress(0)

    for idx, (assignment_name, assignment_text) in enumerate(assignments_text.items()):
        # Initialize report dictionary for this assignment
        compliance_reports[assignment_name] = {}

        # Compliance Checks
        if selected_tools['compliance_checks']:
            if 'assessment_brief' in selected_tools['compliance_checks']:
                try:
                    # Assuming the first assessment brief corresponds to the assignment
                    assessment_brief_text = next(iter(assessment_briefs_text.values()))
                    response = check_assessment_compliance(
                        groq_client,
                        assignment_text,
                        assessment_brief_text
                    )
                    compliance_reports[assignment_name]['Assessment Brief Compliance'] = response
                except Exception as e:
                    compliance_reports[assignment_name]['Assessment Brief Compliance'] = f"🛑 Error: {e}"

            if 'module_materials' in selected_tools['compliance_checks']:
                try:
                    # Assuming the first module material corresponds to the assignment
                    module_material_text = next(iter(module_materials_text.values()))
                    response = check_module_compliance(
                        groq_client,
                        assignment_text,
                        module_material_text
                    )
                    compliance_reports[assignment_name]['Module Materials Compliance'] = response
                except Exception as e:
                    compliance_reports[assignment_name]['Module Materials Compliance'] = f"🛑 Error: {e}"

        # Grammar Check
        if selected_tools['grammar_check']:
            try:
                response = grammar_check(groq_client, assignment_text)
                grammar_reports[assignment_name] = response
            except Exception as e:
                grammar_reports[assignment_name] = f"🛑 Error: {e}"

        # Critical Writing Check
        if selected_tools['critical_writing_check']:
            try:
                response = critical_writing_check(groq_client, assignment_text)
                critical_writing_reports[assignment_name] = response
            except Exception as e:
                critical_writing_reports[assignment_name] = f"🛑 Error: {e}"

        # Reference Check
        if selected_tools['reference_check']:
            reference_style = selected_tools['reference_style']
            if not reference_style:
                reference_reports[assignment_name] = "🛑 No reference style provided."
            else:
                try:
                    # Assuming module materials contain necessary references
                    module_material_text = next(iter(module_materials_text.values()))
                    response = reference_check(
                        groq_client,
                        assignment_text,
                        module_material_text,
                        reference_style=reference_style
                    )
                    reference_reports[assignment_name] = response
                except Exception as e:
                    reference_reports[assignment_name] = f"🛑 Error: {e}"

        progress.progress((idx + 1) / total)

    # Store reports in session state
    st.session_state['compliance_reports'] = compliance_reports
    st.session_state['grammar_reports'] = grammar_reports
    st.session_state['reference_reports'] = reference_reports
    st.session_state['critical_writing_reports'] = critical_writing_reports

    st.success("✅ Analysis completed and reports generated!")

def download_options():
    if 'selected_tools' not in st.session_state:
        return

    selected_tools = st.session_state['selected_tools']
    # Calculate the number of tools used
    tools_used = len(selected_tools['compliance_checks']) + \
                 int(selected_tools['grammar_check']) + \
                 int(selected_tools['critical_writing_check']) + \
                 int(selected_tools['reference_check'])

    if tools_used == 0:
        return

    st.header("📥 Download Reports")

    # Determine if multiple tools were used
    multiple_tools = tools_used > 1

    if multiple_tools:
        download_choice = st.radio(
            "Choose your download option:",
            ["Individual Reports", "Compiled Report"],
            key="download_choice"
        )
    else:
        download_choice = "Individual Reports"

    if st.button("🔽 Download Report"):
        assignments_text = st.session_state['assignments_text']
        for assignment_name, assignment_text in assignments_text.items():
            if download_choice == "Individual Reports":
                # Generate and download individual reports
                compliance_reports = st.session_state['compliance_reports'].get(assignment_name, {})
                grammar_report = st.session_state['grammar_reports'].get(assignment_name, "")
                critical_writing_report = st.session_state['critical_writing_reports'].get(assignment_name, "")
                reference_report = st.session_state['reference_reports'].get(assignment_name, "")

                # List to keep track of available reports
                available_reports = []
                if compliance_reports:
                    for key, content in compliance_reports.items():
                        available_reports.append((key, content))
                if grammar_report:
                    available_reports.append(("Grammar Check", grammar_report))
                if critical_writing_report:
                    available_reports.append(("Critical Writing Check", critical_writing_report))
                if reference_report:
                    available_reports.append(("Reference Check", reference_report))

                for report_title, report_content in available_reports:
                    try:
                        pdf_bytes = generate_individual_pdf_report(
                            report_title,
                            report_content
                        )

                        st.download_button(
                            label=f"📄 Download {report_title} for {assignment_name}",
                            data=pdf_bytes,
                            file_name=f"{assignment_name}_{report_title.replace(' ', '_')}.pdf",
                            mime='application/pdf'
                        )
                    except Exception as e:
                        st.error(f"🛑 Error generating PDF for {report_title} in {assignment_name}: {e}")

            elif download_choice == "Compiled Report":
                # Compile all reports into one PDF per assignment
                reports_dict = {}

                # Compliance Reports
                compliance_reports = st.session_state['compliance_reports'].get(assignment_name, {})
                for key, report_content in compliance_reports.items():
                    reports_dict[key] = report_content

                # Grammar Report
                if assignment_name in st.session_state['grammar_reports']:
                    reports_dict['Grammar Check'] = st.session_state['grammar_reports'][assignment_name]

                # Critical Writing Report
                if assignment_name in st.session_state['critical_writing_reports']:
                    reports_dict['Critical Writing Check'] = st.session_state['critical_writing_reports'][assignment_name]

                # Reference Report
                if assignment_name in st.session_state['reference_reports']:
                    reports_dict['Reference Check'] = st.session_state['reference_reports'][assignment_name]

                try:
                    pdf_bytes = generate_compiled_pdf_report(assignment_name, reports_dict)

                    st.download_button(
                        label=f"📄 Download Compiled QA Report for {assignment_name}",
                        data=pdf_bytes,
                        file_name=f"{assignment_name}_Compiled_QA_Report.pdf",
                        mime='application/pdf'
                    )
                except Exception as e:
                    st.error(f"🛑 Error generating compiled PDF for {assignment_name}: {e}")

def main():
    if selected == "Home":
        home()
        if 'selected_tools' in st.session_state:
            st.write("---")
            download_options()
    elif selected == "Reports":
        import pages.reports
        pages.reports.view_reports()
        pages.reports.download_reports()
    elif selected == "Tutorial":
        import pages.tutorial
        pages.tutorial.main()

if __name__ == "__main__":
    main()
