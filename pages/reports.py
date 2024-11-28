import streamlit as st
from utils.pdf_generation_reportlab import generate_individual_pdf_report

def get_reports_for_assignment(assignment_name):
    reports = {}
    # Compliance Reports
    compliance_reports = st.session_state['compliance_reports'].get(assignment_name, {})
    for key, report_content in compliance_reports.items():
        reports[key] = report_content

    # Grammar Report
    if assignment_name in st.session_state['grammar_reports']:
        reports['Grammar Check'] = st.session_state['grammar_reports'][assignment_name]

    # Critical Writing Report
    if assignment_name in st.session_state['critical_writing_reports']:
        reports['Critical Writing Check'] = st.session_state['critical_writing_reports'][assignment_name]

    # Reference Report
    if assignment_name in st.session_state['reference_reports']:
        reports['Reference Check'] = st.session_state['reference_reports'][assignment_name]

    return reports

def view_reports():
    st.header("📑 View Reports")

    if 'selected_tools' not in st.session_state:
        st.info("🛈 Please run analysis by selecting tools first.")
        return

    assignments = st.session_state['assignments_text']

    for assignment_name in assignments.keys():
        st.subheader(f"📄 Assignment: {assignment_name}")

        reports = get_reports_for_assignment(assignment_name)

        if not reports:
            st.write("🚫 No reports available for this assignment.")
            continue

        tabs = st.tabs(list(reports.keys()))
        for tab, report_title in zip(tabs, reports.keys()):
            with tab:
                report_content = reports[report_title]
                st.markdown(report_content)

def download_reports():
    st.header("📥 Download Reports")

    if 'selected_tools' not in st.session_state:
        st.info("🛈 Please run analysis by selecting tools first.")
        return

    assignments_text = st.session_state['assignments_text']
    selected_tools = st.session_state['selected_tools']

    for assignment_name, _ in assignments_text.items():
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

        if not reports_dict:
            st.write(f"🚫 No reports available for {assignment_name}.")
            continue

        # Dropdown to select which report to download
        report_titles = list(reports_dict.keys())
        selected_report = st.selectbox(
            f"🔽 Select Report to Download for {assignment_name}",
            report_titles,
            key=f"select_report_{assignment_name}"
        )

        if selected_report:
            report_content = reports_dict[selected_report]
            try:
                pdf_bytes = generate_individual_pdf_report(
                    selected_report,
                    report_content
                )

                st.download_button(
                    label=f"📄 Download {selected_report}",
                    data=pdf_bytes,
                    file_name=f"{assignment_name}_{selected_report.replace(' ', '_')}.pdf",
                    mime='application/pdf'
                )
            except Exception as e:
                st.error(f"🛑 Error generating PDF for {selected_report} in {assignment_name}: {e}")

def main():
    view_reports()
    st.write("---")
    download_reports()

if __name__ == "__main__":
    main()
