import streamlit as st
import json
import os
import re
from pathlib import Path
from anthropic import Anthropic

# Page configuration
st.set_page_config(
    page_title="🎲 UKGC Regulatory Framework Navigator",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "documents" not in st.session_state:
    st.session_state.documents = {
        "lccp": [],
        "iso27001": [],
        "rts": []
    }

if "url_mapping" not in st.session_state:
    st.session_state.url_mapping = {}

# Initialize Anthropic client
client = Anthropic()

# Helper function to load JSON files
def load_json_file(filepath):
    """Load and parse a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.warning(f"Could not load {filepath}: {e}")
        return None

# Helper function to get regulation URL
def get_regulation_url(framework: str, doc_id: str) -> str:
    """Get URL for a regulation from the mapping"""
    if not st.session_state.url_mapping:
        return None
    
    # Build the lookup key based on framework and doc_id
    lookup_key = f"{framework}_{doc_id}"
    
    if lookup_key in st.session_state.url_mapping.get("mappings", {}):
        return st.session_state.url_mapping["mappings"][lookup_key].get("url", "")
    
    return None

# Helper function to format regulation as a clickable link
def format_regulation_with_link(framework: str, doc_id: str, title: str) -> str:
    """Format a regulation as a clickable markdown link"""
    url = get_regulation_url(framework, doc_id)
    if url:
        return f"📎 [{framework} {doc_id}: {title}]({url})"
    else:
        return f"📋 {framework} {doc_id}: {title}"

# Load data files on app startup
@st.cache_resource
def load_all_data():
    """Load all JSON files from the JSON Files directory"""
    base_path = Path("JSON Files")
    
    documents = {
        "lccp": [],
        "iso27001": [],
        "rts": []
    }
    
    # Load LCCP files
    lccp_path = base_path / "lccp"
    if lccp_path.exists():
        for file in lccp_path.glob("*.json"):
            data = load_json_file(file)
            if data:
                documents["lccp"].append({
                    "filename": file.name,
                    "data": data
                })
    
    # Load ISO 27001 files
    iso_path = base_path / "iso-27001"
    if iso_path.exists():
        for file in iso_path.glob("*.json"):
            data = load_json_file(file)
            if data:
                documents["iso27001"].append({
                    "filename": file.name,
                    "data": data
                })
    
    # Load RTS files
    rts_path = base_path / "rts"
    if rts_path.exists():
        for file in rts_path.glob("*.json"):
            data = load_json_file(file)
            if data:
                documents["rts"].append({
                    "filename": file.name,
                    "data": data
                })
    
    # Load URL mapping
    url_mapping_path = base_path / "index" / "url_mapping.json"
    url_mapping = {}
    if url_mapping_path.exists():
        url_mapping = load_json_file(url_mapping_path) or {}
    
    return documents, url_mapping

# Load data
documents, url_mapping = load_all_data()
st.session_state.documents = documents
st.session_state.url_mapping = url_mapping

# Header
st.title("🎲 UKGC Regulatory Framework Navigator")
st.markdown("Integrated compliance tool for LCCP, ISO 27001, and RTS frameworks")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("LCCP Documents", len(st.session_state.documents["lccp"]))
with col2:
    st.metric("ISO 27001 Controls", len(st.session_state.documents["iso27001"]))
with col3:
    st.metric("RTS Chapters", len(st.session_state.documents["rts"]))
with col4:
    st.metric("URL Mappings", len(st.session_state.url_mapping.get("mappings", {})))

st.divider()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "❓ Ask a Question", "🔍 Keyword Search", "📚 Browse"])

# Tab 1: Dashboard
with tab1:
    st.subheader("Framework Overview")
    
    st.markdown("""
    ## How the Three Frameworks Work Together
    
    ### 🏛️ LCCP (Licence Conditions and Codes of Practice)
    - **What:** Business and regulatory requirements
    - **Authority:** UK Gambling Commission
    - **Role:** Top-level compliance obligations
    - **Example:** "Operators must prevent underage gambling"
    
    ### 🔒 ISO 27001 (Information Security Management)
    - **What:** Security implementation framework
    - **Authority:** International Organization for Standardization
    - **Role:** How to implement requirements securely
    - **Example:** "Use A_8.5 (Secure Authentication) for age verification"
    
    ### ⚙️ RTS (Remote Technical Standards)
    - **What:** Gambling-specific technical specifications
    - **Authority:** UK Gambling Commission
    - **Role:** Detailed technical how-to
    - **Example:** "RTS-01 specifies exact age verification data format"
    
    ## Compliance Flow
    
    1. **Identify** what you must do (LCCP)
    2. **Design** how to do it securely (ISO 27001)
    3. **Implement** technical specifications (RTS)
    4. **Verify** compliance across all three
    
    ## Key Principles
    
    - All three frameworks are **mandatory** for operators
    - They are **complementary**, not redundant
    - **LCCP** takes precedence over framework guidance
    - **RTS** provides gambling-specific technical detail
    - **ISO 27001** provides international best practices
    """)

# Tab 2: Ask a Question
with tab2:
    st.subheader("Ask a Regulatory Question")
    st.markdown("Ask any question about LCCP, ISO 27001, or RTS compliance requirements")
    
    user_question = st.text_area(
        "Your question:",
        placeholder="e.g., 'What are my customer fund obligations?' or 'How do I implement age verification?'"
    )
    
    if st.button("Get Answer", key="ask_button"):
        if user_question:
            with st.spinner("Searching regulatory documents and formulating answer..."):
                # Add user message to history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": user_question
                })
                
                # Prepare context from documents
                doc_context = "Available LCCP provisions:\n"
                for doc in st.session_state.documents["lccp"]:
                    doc_context += f"- {doc['filename']}\n"
                
                doc_context += "\nAvailable ISO 27001 controls:\n"
                for doc in st.session_state.documents["iso27001"]:
                    doc_context += f"- {doc['filename']}\n"
                
                doc_context += "\nAvailable RTS standards:\n"
                for doc in st.session_state.documents["rts"]:
                    doc_context += f"- {doc['filename']}\n"
                
                # Get response from Claude
                try:
                    response = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2000,
                        system=f"""You are an expert in UK gambling regulation, specifically LCCP (Licence Conditions and Codes of Practice), ISO 27001 (Information Security), and RTS (Remote Technical Standards).

{doc_context}

Provide accurate, cited answers to gambling compliance questions. Reference specific provisions and standards when applicable.""",
                        messages=st.session_state.conversation_history
                    )
                    
                    assistant_message = response.content[0].text
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    st.markdown("### Answer")
                    st.markdown(assistant_message)
                    
                except Exception as e:
                    st.error(f"Error getting response: {str(e)}")
        else:
            st.warning("Please enter a question")

# Tab 3: Keyword Search
with tab3:
    st.subheader("Search by Keyword")
    
    search_term = st.text_input("Enter keyword to search:", placeholder="e.g., 'customer funds', 'age verification'")
    
    if search_term:
        st.markdown("### Search Results")
        
        results_found = False
        
        # Search LCCP
        if st.session_state.documents["lccp"]:
            with st.expander("📋 LCCP Results", expanded=True):
                for doc in st.session_state.documents["lccp"]:
                    doc_data = doc["data"]
                    
                    # Search in sections
                    if "sections" in doc_data:
                        for section in doc_data["sections"]:
                            if search_term.lower() in str(section).lower():
                                results_found = True
                                section_id = section.get("section_id", "")
                                section_title = section.get("section_title", "")
                                
                                st.write(f"**Section {section_id}: {section_title}**")
                                
                                # Search in conditions
                                if "conditions" in section:
                                    for condition in section["conditions"]:
                                        if search_term.lower() in str(condition).lower():
                                            condition_id = condition.get("condition_id", "")
                                            condition_title = condition.get("condition_title", "")
                                            
                                            # Determine the prefix based on filename
                                            if "operating" in doc["filename"].lower():
                                                prefix = "OLC"
                                            elif "code" in doc["filename"].lower():
                                                prefix = "CoP"
                                            elif "personal" in doc["filename"].lower():
                                                prefix = "PLC"
                                            else:
                                                prefix = "OLC"
                                            
                                            full_id = f"{prefix}_{condition_id}"
                                            regulation_link = format_regulation_with_link("LCCP", full_id, condition_title)
                                            st.markdown(regulation_link)
        
        # Search ISO 27001
        if st.session_state.documents["iso27001"]:
            with st.expander("🔒 ISO 27001 Results", expanded=True):
                for doc in st.session_state.documents["iso27001"]:
                    doc_data = doc["data"]
                    
                    if search_term.lower() in str(doc_data).lower():
                        results_found = True
                        
                        if "control_id" in doc_data:
                            control_id = doc_data["control_id"]
                            control_title = doc_data.get("control_title", "")
                            regulation_link = format_regulation_with_link("ISO27001", control_id, control_title)
                            st.markdown(regulation_link)
        
        # Search RTS
        if st.session_state.documents["rts"]:
            with st.expander("⚙️ RTS Results", expanded=True):
                for doc in st.session_state.documents["rts"]:
                    doc_data = doc["data"]
                    
                    if search_term.lower() in str(doc_data).lower():
                        results_found = True
                        
                        # Extract chapter number from filename or data
                        filename = doc["filename"]
                        if "rts" in filename.lower():
                            # Try to extract chapter number
                            parts = filename.replace(".json", "").split("-")
                            chapter_id = parts[-1] if parts[-1].isdigit() else "Unknown"
                            title = doc_data.get("title", "RTS Chapter")
                            regulation_link = format_regulation_with_link("RTS", chapter_id, title)
                            st.markdown(regulation_link)
        
        if not results_found:
            st.info(f"No results found for '{search_term}'")

# Tab 4: Browse
with tab4:
    st.subheader("Browse Regulatory Documents")
    
    browse_option = st.radio("Select framework:", ["LCCP", "ISO 27001", "RTS"], horizontal=True)
    
    if browse_option == "LCCP" and st.session_state.documents["lccp"]:
        st.markdown("### LCCP - Licence Conditions and Codes of Practice")
        
        for doc in st.session_state.documents["lccp"]:
            doc_data = doc["data"]
            filename = doc["filename"]
            
            # Determine prefix from filename
            if "operating" in filename.lower():
                prefix = "OLC"
                file_type = "📋 Operating Licence Conditions (OLC)"
            elif "code" in filename.lower():
                prefix = "CoP"
                file_type = "📝 Code of Practice (CoP)"
            elif "personal" in filename.lower():
                # Skip Personal Licence Conditions for now
                continue
            else:
                prefix = "OLC"
                file_type = "Licence Conditions"
            
            # Display document type header
            st.markdown(f"#### {file_type}")
            
            if "sections" in doc_data:
                for section in doc_data["sections"]:
                    section_id = section.get("section_id", "")
                    section_title = section.get("section_title", "")
                    
                    # Create unique label including prefix to separate OLC/CoP/PLC sections
                    expander_label = f"**{prefix} Section {section_id}: {section_title}**"
                    
                    with st.expander(expander_label):
                        # Handle OLC structure: sections → conditions
                        if "conditions" in section:
                            for condition in section["conditions"]:
                                condition_id = condition.get("condition_id", "")
                                condition_title = condition.get("condition_title", "")
                                
                                full_id = f"{prefix}_{condition_id}"
                                regulation_link = format_regulation_with_link("LCCP", full_id, condition_title)
                                st.markdown(regulation_link)
                        
                        # Handle CoP/PLC structure: sections → subsections → provisions
                        elif "subsections" in section:
                            for subsection in section["subsections"]:
                                subsection_title = subsection.get("subsection_title", "")
                                
                                if subsection_title:
                                    st.markdown(f"**{subsection_title}**")
                                
                                if "provisions" in subsection:
                                    for provision in subsection["provisions"]:
                                        provision_id = provision.get("provision_id", "")
                                        provision_title = provision.get("provision_title", "")
                                        
                                        full_id = f"{prefix}_{provision_id}"
                                        regulation_link = format_regulation_with_link("LCCP", full_id, provision_title)
                                        st.markdown(regulation_link)
            
            st.divider()
    
    elif browse_option == "ISO 27001" and st.session_state.documents["iso27001"]:
        st.markdown("### ISO 27001 - Information Security Management")
        
        # Sort ISO 27001 documents by control number (A.5.1, A.5.2, A.8.1, etc.)
        def get_iso_control_number(doc):
            """Extract control number for sorting (e.g., 5.1 from A 5.1)"""
            doc_data = doc["data"]
            control = doc_data.get("control", {})
            control_number = control.get("control_number", "")
            # Parse "A 5.35" to (5, 35) for sorting
            if "A " in control_number:
                parts = control_number.replace("A ", "").split(".")
                try:
                    return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
                except (ValueError, IndexError):
                    return (999, 999)
            return (999, 999)
        
        sorted_iso_docs = sorted(st.session_state.documents["iso27001"], key=get_iso_control_number)
        
        for doc in sorted_iso_docs:
            doc_data = doc["data"]
            
            if "control" in doc_data:
                control = doc_data["control"]
                control_id = control.get("control_id", "")
                control_number = control.get("control_number", "")
                control_title = control.get("control_title", "")
                control_category = doc_data.get("control_category", "")
                
                with st.expander(f"**{control_number}: {control_title}**", expanded=False):
                    # Display control category
                    if control_category:
                        st.markdown(f"**Category:** {control_category}")
                    
                    # Display control purpose
                    control_purpose = control.get("control_purpose", "")
                    if control_purpose:
                        st.markdown(f"**Purpose:** {control_purpose}")
                    
                    # Display key requirements if available
                    iso_def = doc_data.get("iso_27001_definition", {})
                    key_reqs = iso_def.get("key_requirements", [])
                    if key_reqs:
                        st.markdown("**Key Requirements:**")
                        for req in key_reqs:
                            st.write(f"• {req}")
    
    elif browse_option == "RTS" and st.session_state.documents["rts"]:
        st.markdown("### RTS - Remote Technical Standards")
        
        # Sort RTS documents by chapter number
        def get_rts_chapter_number(doc):
            """Extract chapter number for sorting"""
            filename = doc["filename"]
            chapter_match = re.search(r'rts-(\d+)', filename, re.IGNORECASE)
            if chapter_match:
                return int(chapter_match.group(1))
            return 999  # Put unsorted items at the end
        
        sorted_rts_docs = sorted(st.session_state.documents["rts"], key=get_rts_chapter_number)
        
        for doc in sorted_rts_docs:
            doc_data = doc["data"]
            filename = doc["filename"]
            
            # Skip chapter-4 security requirements for now
            if "chapter-4" in filename.lower():
                continue
            
            # FIXED: Extract chapter number correctly from filename
            # Example: rts-01-customer-account-information.json → chapter_id = "01"
            chapter_match = re.search(r'rts-(\d+)', filename, re.IGNORECASE)
            chapter_id = chapter_match.group(1) if chapter_match else "Unknown"
            
            # Get aim information from the data structure
            aim = doc_data.get("aim", {})
            aim_title = aim.get("aim_title", f"RTS Chapter {chapter_id}")
            aim_description = aim.get("aim_description", "")
            
            # Create main expander for this RTS chapter
            with st.expander(f"**RTS-{chapter_id}: {aim_title}**", expanded=False):
                # Display aim description
                if aim_description:
                    st.markdown("**Aim:**")
                    st.write(aim_description)
                
                # Display the UKGC hyperlink for this RTS section
                regulation_link = format_regulation_with_link("RTS", chapter_id, aim_title)
                st.markdown(f"**Official Documentation:** {regulation_link}")
                
                st.divider()
                
                # Display all requirements under this aim
                if "requirements" in doc_data and doc_data["requirements"]:
                    st.markdown("**Requirements:**")
                    
                    for req in doc_data["requirements"]:
                        req_id = req.get("requirement_id", "Unknown")
                        req_title = req.get("title", "")
                        req_type = req.get("requirement_type", "")
                        
                        # Create sub-expander for each requirement
                        req_expander_label = f"**{req_id}**: {req_title} ({req_type})"
                        with st.expander(req_expander_label, expanded=False):
                            # Display requirement full text
                            full_text = req.get("full_text", "")
                            if full_text:
                                st.markdown("**Requirement:**")
                                st.write(full_text)
                            
                            # Display implementation guidance if available
                            impl_guidance = req.get("implementation_guidance", {})
                            if impl_guidance:
                                st.markdown("**Implementation Guidance:**")
                                
                                # Display key points if available
                                key_points = impl_guidance.get("key_points", [])
                                if key_points:
                                    st.markdown("*Key Points:*")
                                    for point in key_points:
                                        st.write(f"- {point}")
                                
                                # Display any structured guidance
                                guidance_text = impl_guidance.get("full_text", "")
                                if guidance_text:
                                    st.write(guidance_text)
                else:
                    st.info("No requirements found for this RTS section.")
            
            st.divider()

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📋 URL Mapping Status")
    
    if st.session_state.url_mapping:
        mappings = st.session_state.url_mapping.get("mappings", {})
        
        lccp_urls = sum(1 for k in mappings if k.startswith("LCCP_"))
        rts_urls = sum(1 for k in mappings if k.startswith("RTS_"))
        
        st.write(f"**LCCP URLs:** {lccp_urls}")
        st.write(f"**RTS URLs:** {rts_urls}")
        st.write(f"**Total Mappings:** {len(mappings)}")
        
        with st.expander("View All Mappings"):
            for key, value in sorted(mappings.items()):
                st.write(f"- **{key}**: {value.get('title', 'N/A')}")
    else:
        st.warning("URL mapping file not loaded")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    This navigator integrates:
    - **LCCP**: Operating Licence Conditions & Code of Practice
    - **ISO 27001**: Information Security Management
    - **RTS**: Remote Technical Standards
    
    All maintained by the UK Gambling Commission.
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    UKGC Regulatory Framework Navigator | Integrated LCCP, ISO 27001, and RTS Compliance Tool
</div>
""", unsafe_allow_html=True)
