"""
UKGC Regulatory Framework - Streamlit Web Interface
Multi-framework compliance querying and guidance
WITH CLAUDE AI - Natural language question answering
WITH HYPERLINKS - URL mapping for clickable regulations
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


def load_url_mapping():
    """Load URL mapping for hyperlinks"""
    base_path = Path(__file__).parent / "JSON Files"
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
    """Get URL for a regulation from the URL mapping."""
    if not st.session_state.url_mapping:
        return None
    
    mappings = st.session_state.url_mapping.get('mappings', {})
    if not mappings:
        return None
    
    fw_upper = framework.upper().replace(" ", "").strip()
    lookup_attempts = []
    
    if fw_upper == "RTS":
        match = re.search(r'(\d+)', regulation_id)
        if match:
            aim_number = match.group(1)
            lookup_attempts.extend([
                f"RTS_{aim_number.zfill(2)}",
                f"RTS_{aim_number}",
                regulation_id,
            ])
    elif fw_upper == "LCCP":
        lookup_attempts.extend([
            f"LCCP_{regulation_id}",
            regulation_id,
        ])
    else:
        lookup_attempts.extend([
            f"{fw_upper}_{regulation_id}",
            regulation_id,
        ])
    
    for lookup_key in lookup_attempts:
        if lookup_key in mappings:
            url = mappings[lookup_key].get('url')
            if url:
                return url
    
    return None


def format_regulation_with_link(framework: str, doc_id: str, title: str) -> str:
    """Format a regulation as a clickable markdown link"""
    url = get_regulation_url(framework, doc_id)
    if url:
        return f"📎 [{framework} {doc_id}: {title}]({url})"
    else:
        return f"📋 {framework} {doc_id}: {title}"


def extract_document_ids_from_lccp(content: Dict) -> List[tuple]:
    """Extract LCCP condition IDs and titles"""
    ids = []
    if "conditions" in content:
        for condition in content["conditions"]:
            condition_id = condition.get('condition_id', '')
            condition_title = condition.get('condition_title', 'Untitled')
            if condition_id:
                ids.append((condition_id, condition_title))
    return ids


def extract_document_ids_from_rts(content: Dict) -> List[tuple]:
    """Extract RTS Aim IDs and descriptions"""
    ids = []
    if "aim" in content:
        aim_id = content["aim"].get('aim_id', '')
        aim_desc = content["aim"].get('aim_description', 'Untitled')
        if aim_id:
            ids.append((aim_id, aim_desc))
    return ids


def search_documents(query: str) -> List[Dict]:
    """Search all documents for a keyword"""
    results = []
    query_lower = query.lower()
    
    for doc in st.session_state.documents["lccp"]:
        content = doc['content']
        for condition in content.get("conditions", []):
            condition_id = condition.get('condition_id', '')
            condition_title = condition.get('condition_title', '')
            condition_text = condition.get('condition_text', '')
            
            if (query_lower in condition_id.lower() or 
                query_lower in condition_title.lower() or 
                query_lower in condition_text.lower()):
                results.append({
                    'framework': 'lccp',
                    'id': condition_id,
                    'title': condition_title,
                    'relevance': 'high' if query_lower in condition_title.lower() else 'medium'
                })
    
    for doc in st.session_state.documents["iso27001"]:
        control = doc["content"].get("control", {})
        control_id = control.get('control_id', '')
        control_title = control.get('control_title', '')
        control_text = control.get('control_objective', '')
        
        if (query_lower in control_id.lower() or 
            query_lower in control_title.lower() or 
            query_lower in control_text.lower()):
            results.append({
                'framework': 'iso27001',
                'id': control_id,
                'title': control_title,
                'relevance': 'high' if query_lower in control_title.lower() else 'medium'
            })
    
    for doc in st.session_state.documents["rts"]:
        content = doc['content']
        aim_data = content.get('aim', {})
        aim_id = aim_data.get('aim_id', '')
        aim_desc = aim_data.get('aim_description', '')
        aim_text = aim_data.get('aim_details', '')
        
        if (query_lower in aim_id.lower() or 
            query_lower in aim_desc.lower() or 
            query_lower in aim_text.lower()):
            results.append({
                'framework': 'rts',
                'id': aim_id,
                'title': aim_desc,
                'relevance': 'high' if query_lower in aim_desc.lower() else 'medium'
            })
    
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results


def answer_with_ai(question: str, client) -> tuple:
    """Use Claude AI to answer questions about regulations"""
    search_results = search_documents(question)
    relevant_docs = []
    
    context = ""
    if search_results:
        context = "Relevant regulatory documents:\n\n"
        for doc in search_results[:10]:
            relevant_docs.append(doc)
            content = None
            
            if doc['framework'] == 'iso27001':
                for d in st.session_state.documents['iso27001']:
                    if d['content'].get('control', {}).get('control_id') == doc['id']:
                        content = d['content'].get('control', {})
                        break
                if content:
                    context += f"ISO 27001 {doc['id']}: {doc['title']}\n"
                    context += f"   Objective: {content.get('control_objective', '')}\n"
                    context += f"   Purpose: {content.get('control_purpose', '')}\n"
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
                rts_ids = extract_document_ids_from_rts(content)
                for rts_id, rts_title in rts_ids:
                    regulation_link = format_regulation_with_link("RTS", rts_id, rts_title)
                    st.markdown(regulation_link)

# ============ URL MAPPING STATUS ============
st.divider()
if st.session_state.url_mapping:
    st.markdown("### 📋 URL Mapping Status")
    mappings = st.session_state.url_mapping.get('mappings', {})
    
    lccp_urls = [k for k in mappings.keys() if k.startswith('LCCP_')]
    rts_urls = [k for k in mappings.keys() if k.startswith('RTS_')]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("LCCP URLs Mapped", len(lccp_urls))
    with col2:
        st.metric("RTS URLs Mapped", len(rts_urls))
    
    st.info("✅ URL mapping loaded successfully. Hyperlinks are active in search results and browse sections.")
    
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
