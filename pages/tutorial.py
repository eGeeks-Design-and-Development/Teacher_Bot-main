import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
        /* Custom Card Container */
        .feature-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid rgba(230, 230, 230, 0.5);
            backdrop-filter: blur(10px);
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        /* Card Header */
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 0.8rem;
        }
        
        .card-icon {
            font-size: 1.8rem;
            margin-right: 1rem;
            background: linear-gradient(45deg, #2196F3, #00BCD4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .card-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #1a237e;
            margin: 0;
        }
        
        /* List Styling */
        .custom-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .custom-list li {
            position: relative;
            padding: 0.5rem 0 0.5rem 2rem;
            color: #424242;
            transition: color 0.3s ease;
        }
        
        .custom-list li:before {
            content: '→';
            position: absolute;
            left: 0;
            color: #2196F3;
            font-weight: bold;
            transition: transform 0.3s ease;
        }
        
        .custom-list li:hover {
            color: #1565C0;
        }
        
        .custom-list li:hover:before {
            transform: translateX(5px);
        }
        
        /* Grid Layout */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            padding: 1rem;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .grid-container {
                grid-template-columns: 1fr;
            }
            
            .feature-card {
                margin: 0.5rem 0;
            }
        }
        
        /* Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease forwards;
        }
        </style>
    """, unsafe_allow_html=True)

def create_feature_card(icon, title, items):
    return f"""
        <div class="feature-card fade-in">
            <div class="card-header">
                <span class="card-icon">{icon}</span>
                <h3 class="card-title">{title}</h3>
            </div>
            <ul class="custom-list">
                {' '.join(f'<li>{item}</li>' for item in items)}
            </ul>
        </div>
    """

def main():
    inject_custom_css()
    
    # Header
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #90caf9, #0d47a1); 
             border-radius: 16px; margin-bottom: 2rem; color: white;">
            <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎓 Academic QA Guide</h1>
            <p style="font-size: 1.2rem; opacity: 0.9;">Master Your Academic Analysis</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards Grid
    st.markdown("""
        <div class="grid-container">
            {}
        </div>
    """.format(
        ''.join([
            create_feature_card("📤", "Upload", [
                "Drop your files (PDF/DOCX/PPTX)",
                "Include assignments & briefs",
                "Click 'Process Files'"
            ]),
            create_feature_card("🔍", "Analyze", [
                "Pick analysis tools",
                "Set reference style",
                "Hit 'Analyze'"
            ]),
            create_feature_card("📊", "Review", [
                "Check detailed reports",
                "Download results",
                "Track improvements"
            ]),
            create_feature_card("💡", "Pro Tips", [
                "Use multiple tools",
                "Check institution guidelines",
                "Save reports promptly"
            ])
        ])
    ), unsafe_allow_html=True)
    
    # Tools Section with Modern Tabs
    st.markdown("""
        <div style="margin-top: 2rem; padding: 1.5rem; background: rgba(255, 255, 255, 0.95); 
             border-radius: 16px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);">
            <h3 style="color: #1a237e; margin-bottom: 1rem;">🛠️ Available Tools</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div class="tool-item">• ✅ Compliance Check</div>
                <div class="tool-item">• 📝 Grammar Check</div>
                <div class="tool-item">• 🎯 Critical Writing</div>
                <div class="tool-item">• 📚 Reference Check</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Help Section
    with st.expander("Need Help? 🤔"):
        st.markdown("""
            <div style="padding: 1rem; background: #f5f5f5; border-radius: 8px;">
                <h4 style="color: #1a237e;">Support Options</h4>
                <ul style="list-style-type: none; padding-left: 0;">
                    <li style="margin: 0.5rem 0;">📧 Email: support@egeeksglobal.com</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()