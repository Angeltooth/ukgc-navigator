"""
UKGC Regulatory Framework - Streamlit Web Interface
Multi-framework compliance querying and guidance
WITH CLAUDE AI - Natural language question answering
WITH HYPERLINKS - URL mapping for clickable regulations
FIXED - Proper document ID and URL mapping matching
"""

import streamlit as st
import json
import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

# Initialize Anthropic client

def get_anthropic_client():
    """Get Anthropic client"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic()

# Page configuration
st.set_page_config(
    page_title="UKGC Regulatory Framework",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    .framework-lccp { color: #1f77b4; }
    .framework-iso { color: #ff7f0e; }
    .framework-rts { color: #2ca02c; }
    .regulation-link {
        color: #0066cc;
        text-decoration: none;
        font-weight: 600;
    }
    .regulation-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)



def load_documents():
    """Load all regulatory documents from JSON files"""
    # Use relative path for Streamlit Cloud compatibility
    base_path = Path(__file__).parent / "JSON Files"
    documents = {
        "lccp": [],
        "iso27001": [],
        "rts": [],
        "indexes": {}
    }
    
    if not base_path.exists():
        st.error(f"❌ Base path not found: {base_path}")
        st.info("Please ensure your project folder exists at: ~/UKGC_Project/JSON Files")
        return documents
    
    try:
        # Load LCCP documents
        lccp_path = base_path / "lccp"
        if lccp_path.exists():
            for file in lccp_path.glob("*.json"):
                try:
                    with open(file, encoding='utf-8') as f:
                        documents["lccp"].append({
                            "filename": file.name,
                            "content": json.load(f)
                        })
                except json.JSONDecodeError as e:
                    st.warning(f"Invalid JSON in {file.name}: {str(e)}")
                except Exception as e:
                    st.warning(f"Error loading LCCP {file.name}: {str(e)}")
        
        # Load ISO 27001 documents
        iso_path = base_path / "iso-27001"
        if iso_path.exists():
            for file in iso_path.glob("*.json"):
                try:
                    with open(file, encoding='utf-8') as f:
                        documents["iso27001"].append({
                            "filename": file.name,
                            "content": json.load(f)
                        })
                except json.JSONDecodeError as e:
                    st.warning(f"Invalid JSON in {file.name}: {str(e)}")
                except Exception as e:
                    st.warning(f"Error loading ISO27001 {file.name}: {str(e)}")
        
        # Load RTS documents
        rts_path = base_path / "rts"
        if rts_path.exists():
            for file in rts_path.glob("*.json"):
                try:
                    with open(file, encoding='utf-8') as f:
                        documents["rts"].append({
                            "filename": file.name,
                            "content": json.load(f)
                        })
                except json.JSONDecodeError as e:
                    st.warning(f"Invalid JSON in {file.name}: {str(e)}")
                except Exception as e:
                    st.warning(f"Error loading RTS {file.name}: {str(e)}")
        
        # Load index documents
        index_path = base_path / "index"
        if index_path.exists():
            for file in index_path.glob("*.json"):
                try:
                    with open(file, encoding='utf-8') as f:
                        documents["indexes"][file.stem] = json.load(f)
                except json.JSONDecodeError as e:
                    st.warning(f"Invalid JSON in {file.name}: {str(e)}")
                except Exception as e:
                    st.warning(f"Error loading index {file.name}: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
    
    return documents


@st.cache_resource
def load_url_mapping():
    """Load URL mapping for hyperlinks"""
    base_path = Path(os.path.expanduser("~/UKGC_Project/JSON Files"))
    url_mapping_path = base_path / "index" / "url_mapping.json"
    
    if url_mapping_path.exists():
        try:
            with open(url_mapping_path, encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            st.warning(f"Invalid JSON in url_mapping.json: {str(e)}")
            return None
        except Exception as e:
            st.warning(f"Error loading url_mapping.json: {str(e)}")
            return None
    else:
        st.warning(f"url_mapping.json not found at {url_mapping_path}")
        return None


def get_regulation_url(framework: str, regulation_id: str) -> Optional[str]:
    """
    Get URL for a regulation from the URL mapping.
    Handles various document ID formats and frameworks.
    """
    if not st.session_state.url_mapping:
        return None
    
    mappings = st.session_state.url_mapping.get('mappings', {})
    if not mappings:
        return None
    
    # Normalize framework name
    fw_upper = framework.upper().replace(" ", "").strip()
    
    # Build lookup attempts - prioritize most specific formats
    lookup_attempts = []
    
    # For RTS: "RTS Aim 12" or "RTS_AIM_12" should lookup "RTS_12"
    if fw_upper == "RTS":
        # Extract number from formats like "RTS Aim 12", "RTS_AIM_12", "RTS_12A", etc
        match = re.search(r'(\d+)', regulation_id)
        if match:
            aim_number = match.group(1)
            # Try common RTS formats
            lookup_attempts.extend([
                f"RTS_{aim_number.zfill(2)}",  # RTS_12
                f"RTS_{aim_number}",            # RTS_12 (without zero-padding)
                regulation_id,                  # Original ID
            ])
    
    # For LCCP: use format like "LCCP_1.1.1"
    elif fw_upper == "LCCP":
        lookup_attempts.extend([
            f"LCCP_{regulation_id}",  # LCCP_1.1.1
            regulation_id,             # Original ID
        ])
    
    # General fallback
    else:
        lookup_attempts.extend([
            f"{fw_upper}_{regulation_id}",
            regulation_id,
        ])
    
    # Try each lookup attempt
    for lookup_key in lookup_attempts:
        if lookup_key in mappings:
            url = mappings[lookup_key].get('url')
            if url:
                return url
    
    return None


def extract_document_ids_from_lccp(lccp_content: dict) -> List[tuple]:
    """
    Extract document IDs and titles from LCCP document.
    Returns list of (id, title) tuples
    """
    results = []
    
    # Navigate through sections and conditions
    if 'sections' in lccp_content:
        for section in lccp_content['sections']:
            if 'conditions' in section:
                for condition in section['conditions']:
                    condition_id = condition.get('condition_id', 'Unknown')
                    condition_title = condition.get('condition_title', 'Untitled')
                    results.append((condition_id, condition_title))
    
    return results


def extract_document_ids_from_rts(rts_content: dict) -> List[tuple]:
    """
    Extract document IDs and titles from RTS document.
    Returns list of (id, title) tuples
    """
    results = []
    
    # RTS format: aim_id or requirement_id
    aim = rts_content.get('aim', {})
    if aim:
        aim_id = aim.get('aim_id', 'Unknown')
        aim_number = aim.get('aim_number', 'Unknown')
        aim_title = aim.get('aim_title', 'Untitled')
        # Use just the number for URL lookup
        results.append((f"RTS Aim {aim_number}", aim_title))
    
    return results


def format_regulation_with_link(framework: str, regulation_id: str, title: str) -> str:
    """Format regulation as markdown link if URL exists, otherwise as plain text"""
    url = get_regulation_url(framework, regulation_id)
    
    if url:
        return f"🔗 [{framework} {regulation_id}: {title}]({url})"
    else:
        return f"📄 {framework} {regulation_id}: {title}"


def search_documents(query: str, framework: Optional[str] = None) -> list:
    """Search across documents"""
    results = []
    query_lower = query.lower()
    
    frameworks_to_search = [framework] if framework else ["lccp", "iso27001", "rts"]
    
    for fw in frameworks_to_search:
        if fw not in st.session_state.documents:
            continue
            
        for doc in st.session_state.documents[fw]:
            content_str = json.dumps(doc["content"]).lower()
            
            if query_lower in content_str:
                if fw == "iso27001":
                    control = doc["content"].get("control", {})
                    doc_id = control.get("control_id", "Unknown")
                    doc_title = control.get("control_title", "Untitled")
                    results.append({
                        "framework": fw,
                        "filename": doc["filename"],
                        "title": doc_title,
                        "id": doc_id,
                        "content": doc["content"],
                        "relevance": content_str.count(query_lower)
                    })
                elif fw == "lccp":
                    # For LCCP, extract condition IDs from sections
                    lccp_ids = extract_document_ids_from_lccp(doc["content"])
                    for cond_id, cond_title in lccp_ids:
                        results.append({
                            "framework": fw,
                            "filename": doc["filename"],
                            "title": cond_title,
                            "id": cond_id,
                            "content": doc["content"],
                            "relevance": content_str.count(query_lower)
                        })
                else:  # rts
                    # For RTS, extract aim IDs
                    rts_ids = extract_document_ids_from_rts(doc["content"])
                    for rts_id, rts_title in rts_ids:
                        results.append({
                            "framework": fw,
                            "filename": doc["filename"],
                            "title": rts_title,
                            "id": rts_id,
                            "content": doc["content"],
                            "relevance": content_str.count(query_lower)
                        })
    
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:20]


def answer_with_ai(question: str, client: Any) -> tuple:
    """Answer question using Claude AI with intelligent document selection"""
    
    # Build summary of all available documents
    summary = "LCCP CONDITIONS:\n"
    if st.session_state.documents.get('lccp'):
        for doc in st.session_state.documents['lccp']:
            lccp_ids = extract_document_ids_from_lccp(doc['content'])
            for cond_id, cond_title in lccp_ids:
                summary += f"  - LCCP {cond_id}: {cond_title}\n"
    
    summary += "\nRTS AIMS:\n"
    if st.session_state.documents.get('rts'):
        for doc in st.session_state.documents['rts']:
            rts_ids = extract_document_ids_from_rts(doc['content'])
            for rts_id, rts_title in rts_ids:
                summary += f"  - {rts_id}: {rts_title}\n"
    
    summary += "\nISO 27001 CONTROLS:\n"
    if st.session_state.documents.get('iso27001'):
        for doc in st.session_state.documents['iso27001']:
            control = doc['content'].get('control', {})
            control_id = control.get('control_id', '')
            control_title = control.get('control_title', '')
            summary += f"  - ISO 27001 {control_id}: {control_title}\n"
    
    # Ask Claude to select relevant documents
    selection_prompt = f"""You are an expert on UKGC regulations. A user has asked a compliance question.

Here are all available regulatory documents:

{summary}

USER QUESTION: {question}

Based on this question, identify which regulatory documents are MOST RELEVANT. Return ONLY a comma-separated list of the document IDs (like "LCCP 1.1.1", "RTS Aim 12", etc.) that would help answer this question. List 3-5 of the most relevant ones. Return ONLY the IDs, nothing else."""
    
    relevant_docs = []
    
    try:
        # Get Claude's selection
        selection_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {"role": "user", "content": selection_prompt}
            ]
        )
        
        selected_ids_text = selection_response.content[0].text.strip()
        selected_ids = [id.strip() for id in selected_ids_text.split(',')]
        
        # Find the actual documents matching these IDs
        for fw in ["lccp", "rts", "iso27001"]:
            if fw not in st.session_state.documents:
                continue
            
            for doc in st.session_state.documents[fw]:
                if fw == "lccp":
                    lccp_ids = extract_document_ids_from_lccp(doc['content'])
                    for cond_id, cond_title in lccp_ids:
                        for sel_id in selected_ids:
                            if cond_id in sel_id or sel_id in f"LCCP {cond_id}":
                                relevant_docs.append({
                                    "framework": fw,
                                    "id": cond_id,
                                    "title": cond_title,
                                    "content": doc['content']
                                })
                
                elif fw == "rts":
                    rts_ids = extract_document_ids_from_rts(doc['content'])
                    for rts_id, rts_title in rts_ids:
                        for sel_id in selected_ids:
                            if str(rts_id).lower() in sel_id.lower() or sel_id.lower() in str(rts_id).lower():
                                relevant_docs.append({
                                    "framework": fw,
                                    "id": rts_id,
                                    "title": rts_title,
                                    "content": doc['content']
                                })
                
                elif fw == "iso27001":
                    control = doc['content'].get('control', {})
                    control_id = control.get('control_id', '')
                    control_title = control.get('control_title', '')
                    for sel_id in selected_ids:
                        if control_id and (control_id in sel_id or sel_id in control_id):
                            relevant_docs.append({
                                "framework": fw,
                                "id": control_id,
                                "title": control_title,
                                "content": doc['content']
                            })
        
        # Fallback: if no matches found, get first of each type
        if not relevant_docs:
            if st.session_state.documents.get('lccp'):
                doc = st.session_state.documents['lccp'][0]
                lccp_ids = extract_document_ids_from_lccp(doc['content'])
                if lccp_ids:
                    cond_id, cond_title = lccp_ids[0]
                    relevant_docs.append({
                        "framework": "lccp",
                        "id": cond_id,
                        "title": cond_title,
                        "content": doc['content']
                    })
            
            if st.session_state.documents.get('rts'):
                doc = st.session_state.documents['rts'][0]
                rts_ids = extract_document_ids_from_rts(doc['content'])
                if rts_ids:
                    rts_id, rts_title = rts_ids[0]
                    relevant_docs.append({
                        "framework": "rts",
                        "id": rts_id,
                        "title": rts_title,
                        "content": doc['content']
                    })
            
            if st.session_state.documents.get('iso27001'):
                doc = st.session_state.documents['iso27001'][0]
                control = doc['content'].get('control', {})
                control_id = control.get('control_id', '')
                control_title = control.get('control_title', '')
                if control_id:
                    relevant_docs.append({
                        "framework": "iso27001",
                        "id": control_id,
                        "title": control_title,
                        "content": doc['content']
                    })
    
    except Exception as e:
        st.warning(f"Issue selecting documents: {str(e)}")
    
    # Build context from selected documents
    context = ""
    if relevant_docs:
        context = "Here are the relevant regulatory documents for this question:\n\n"
        for i, doc in enumerate(relevant_docs[:5], 1):
            context += f"{i}. **{doc['framework'].upper()} - {doc['id']}: {doc['title']}**\n"
            
            content = doc['content']
            if doc['framework'] == 'iso27001':
                control = content.get("control", {})
                if "control_purpose" in control:
                    context += f"   Purpose: {control.get('control_purpose', '')}\n"
            elif doc['framework'] == 'lccp':
                if "document_overview" in content:
                    context += f"   Overview: {content.get('document_overview', '')}\n"
            elif doc['framework'] == 'rts':
                if "aim" in content:
                    aim_desc = content.get('aim', {}).get('aim_description', '')
                    context += f"   Description: {aim_desc}\n"
            context += "\n"
    else:
        context = "Available regulatory frameworks: LCCP (Licence Conditions), RTS (Remote Technical Standards), ISO 27001 (Security)."
    
    system_prompt = """You are an expert on UK Gambling Commission (UKGC) regulations. 
You help operators understand compliance requirements across three frameworks:
1. LCCP (Licence Conditions and Codes of Practice) - Business requirements
2. ISO 27001 - Information security implementation  
3. RTS (Remote Technical Standards) - Gambling-specific technical specifications

When answering questions, cite specific regulatory provisions and explain what operators need to do.
Be clear, practical, and focused on compliance requirements."""
    
    user_prompt = f"""Based on the following regulatory documents, please answer this question:

QUESTION: {question}

REGULATORY CONTEXT:
{context}

Please provide:
1. A direct answer to the question
2. Which frameworks this relates to (LCCP, ISO 27001, RTS)
3. Specific provisions or requirements to follow
4. Any practical steps the operator should take"""
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.content[0].text, relevant_docs
    except Exception as e:
        return f"Error generating answer: {str(e)}", relevant_docs


# Initialize session state
if "documents" not in st.session_state:
    st.session_state.documents = load_documents()

if "url_mapping" not in st.session_state:
    st.session_state.url_mapping = load_url_mapping()

# Header
st.title("🎲 UKGC Regulatory Framework Navigator")
st.markdown("AI-Powered Compliance Tool with Hyperlinks to Official Regulations")

# Check for API key
client = get_anthropic_client()
if not client:
    st.warning("⚠️ To enable AI answers, create ~/.env file with: ANTHROPIC_API_KEY=your_key")
else:
    st.success("✅ AI-powered natural language queries enabled!")

# Show stats
total_docs = (len(st.session_state.documents['lccp']) + 
              len(st.session_state.documents['iso27001']) + 
              len(st.session_state.documents['rts']))

if total_docs > 0:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("LCCP", len(st.session_state.documents['lccp']))
    with col2:
        st.metric("ISO 27001", len(st.session_state.documents['iso27001']))
    with col3:
        st.metric("RTS", len(st.session_state.documents['rts']))
    with col4:
        url_count = len([k for k in st.session_state.url_mapping.get('mappings', {}).keys()]) if st.session_state.url_mapping else 0
        st.metric("URLs Mapped", url_count)

# Tabs
tab1, tab2, tab3 = st.tabs(["🤖 Ask a Question", "🔍 Keyword Search", "📚 Browse"])

# ============ TAB 1: AI Q&A ============
with tab1:
    st.subheader("Ask a Compliance Question")
    
    if not client:
        st.error("AI features not available. Please set ANTHROPIC_API_KEY in ~/.env file")
        st.info("Example questions:\n- How do I prevent underage gambling?\n- What are customer fund protection requirements?\n- How should I implement secure authentication?")
    else:
        st.write("Examples:\n- How do I prevent underage gambling?\n- What are my customer fund protection obligations?\n- How should I implement secure authentication?")
        
        question = st.text_area("Your question:", placeholder="e.g., How do I prevent underage gambling?", height=100)
        
        if st.button("Ask", type="primary"):
            if question:
                with st.spinner("🤔 Analyzing regulatory requirements..."):
                    answer, relevant_docs = answer_with_ai(question, client)
                    
                    st.markdown("### 📖 Answer:")
                    st.markdown(answer)
                    
                    if relevant_docs:
                        st.divider()
                        st.markdown("### 📚 Related Documents:")
                        for doc in relevant_docs[:5]:
                            framework = doc['framework'].upper()
                            doc_id = doc['id']
                            title = doc['title']
                            
                            # Format with hyperlink
                            regulation_link = format_regulation_with_link(framework, doc_id, title)
                            st.markdown(regulation_link)

# ============ TAB 2: Keyword Search ============
with tab2:
    st.subheader("Keyword Search")
    
    search_query = st.text_input("Search term:", placeholder="e.g., 'customer funds', 'authentication'")
    
    if search_query:
        results = search_documents(search_query)
        
        if results:
            st.success(f"Found {len(results)} results")
            for result in results:
                framework = result['framework'].upper()
                doc_id = result['id']
                title = result['title']
                
                # Format with hyperlink
                regulation_link = format_regulation_with_link(framework, doc_id, title)
                st.markdown(regulation_link)
        else:
            st.warning("No results found")

# ============ TAB 3: Browse ============
with tab3:
    st.subheader("Browse Documents")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎲 LCCP")
        if st.checkbox("Show LCCP Documents"):
            for doc in st.session_state.documents["lccp"]:
                content = doc['content']
                
                # Extract conditions from LCCP
                lccp_ids = extract_document_ids_from_lccp(content)
                for condition_id, condition_title in lccp_ids:
                    regulation_link = format_regulation_with_link("LCCP", condition_id, condition_title)
                    st.markdown(regulation_link)
    
    with col2:
        st.markdown("### 🔒 ISO 27001")
        if st.checkbox("Show ISO 27001 Documents"):
            for doc in st.session_state.documents["iso27001"]:
                control = doc["content"].get("control", {})
                control_id = control.get('control_id', '')
                control_title = control.get('control_title', 'Untitled')
                st.write(f"📄 ISO 27001 {control_id}: {control_title}")
    
    with col3:
        st.markdown("### ⚙️ RTS")
        if st.checkbox("Show RTS Documents"):
            for doc in st.session_state.documents["rts"]:
                content = doc['content']
                
                # Extract RTS aim IDs
                rts_ids = extract_document_ids_from_rts(content)
                for rts_id, rts_title in rts_ids:
                    regulation_link = format_regulation_with_link("RTS", rts_id, rts_title)
                    st.markdown(regulation_link)

# ============ URL MAPPING STATUS ============
with st.expander("📋 URL Mapping Status"):
    if st.session_state.url_mapping:
        mappings = st.session_state.url_mapping.get('mappings', {})
        
        lccp_urls = [k for k in mappings.keys() if k.startswith('LCCP_')]
        rts_urls = [k for k in mappings.keys() if k.startswith('RTS_')]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("LCCP URLs Mapped", len(lccp_urls))
        with col2:
            st.metric("RTS URLs Mapped", len(rts_urls))
        
        st.info("✅ URL mapping loaded successfully. Hyperlinks are active in search results and browse sections.")
        
        # Debug info for troubleshooting
        with st.expander("🔍 Debug: Sample URL Mappings"):
            st.write("**Sample LCCP URLs:**")
            for key in lccp_urls[:5]:
                st.write(f"- {key}")
            
            st.write("**Sample RTS URLs:**")
            for key in rts_urls[:5]:
                st.write(f"- {key}")
    else:
        st.error("❌ URL mapping not loaded. Hyperlinks will not be available.")
        st.info("Make sure url_mapping.json exists at: JSON Files/index/url_mapping.json")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    UKGC Regulatory Framework Navigator | Powered by Claude AI | Hyperlinks to Official UKGC Regulations
</div>
""", unsafe_allow_html=True)
