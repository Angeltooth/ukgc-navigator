"""
Cross-Framework Index Builder
Builds a unified, searchable index of LCCP, RTS, and ISO 27001 for Q&A
"""

def build_framework_context(documents):
    """
    Build rich context string for LLM from all frameworks
    """
    context_parts = []
    
    # LCCP Context
    context_parts.append("=" * 80)
    context_parts.append("LCCP (Licence Conditions and Codes of Practice)")
    context_parts.append("=" * 80)
    
    for doc in documents["lccp"]:
        doc_data = doc["data"]
        doc_ref = doc_data.get("document_reference", "LCCP")
        
        if "sections" in doc_data:
            for section in doc_data["sections"]:
                section_id = section.get("section_id", "")
                section_title = section.get("section_title", "")
                
                context_parts.append(f"\n{doc_ref} Section {section_id}: {section_title}")
                
                # Handle conditions
                if "conditions" in section:
                    for condition in section["conditions"]:
                        condition_id = condition.get("condition_id", "")
                        condition_title = condition.get("condition_title", "")
                        condition_text = condition.get("condition_text", "")[:200]  # First 200 chars
                        context_parts.append(f"  - {condition_id}: {condition_title}")
                
                # Handle subsections/provisions
                if "subsections" in section:
                    for subsection in section["subsections"]:
                        if "provisions" in subsection:
                            for provision in subsection["provisions"]:
                                prov_id = provision.get("provision_id", "")
                                prov_title = provision.get("provision_title", "")
                                context_parts.append(f"  - {prov_id}: {prov_title}")
    
    # RTS Context
    context_parts.append("\n" + "=" * 80)
    context_parts.append("RTS (Remote Technical Standards)")
    context_parts.append("=" * 80)
    
    for doc in documents["rts"]:
        doc_data = doc["data"]
        
        # Skip chapter-4
        if "chapter-4" in doc.get("filename", "").lower():
            continue
        
        aim = doc_data.get("aim", {})
        aim_title = aim.get("aim_title", "")
        aim_id = aim.get("aim_number", "")
        
        context_parts.append(f"\nRTS-{aim_id}: {aim_title}")
        
        if "requirements" in doc_data:
            for req in doc_data["requirements"]:
                req_id = req.get("requirement_id", "")
                req_title = req.get("title", "")
                context_parts.append(f"  - {req_id}: {req_title}")
    
    # ISO 27001 Context
    context_parts.append("\n" + "=" * 80)
    context_parts.append("ISO 27001 (Information Security Management)")
    context_parts.append("=" * 80)
    
    for doc in documents["iso27001"]:
        doc_data = doc["data"]
        
        if "control" in doc_data:
            control = doc_data["control"]
            control_num = control.get("control_number", "")
            control_title = control.get("control_title", "")
            category = doc_data.get("control_category", "")
            
            context_parts.append(f"\n{control_num}: {control_title} ({category})")
            
            # Add key requirements
            iso_def = doc_data.get("iso_27001_definition", {})
            key_reqs = iso_def.get("key_requirements", [])
            if key_reqs:
                for req in key_reqs[:3]:  # First 3 key requirements
                    context_parts.append(f"  - {req}")
    
    return "\n".join(context_parts)


def get_enhanced_system_prompt(framework_context):
    """
    Get enhanced system prompt with framework guidance
    """
    return f"""You are an expert in UK gambling regulation. You have access to three frameworks:

1. LCCP (Licence Conditions and Codes of Practice) - What operators MUST do
2. RTS (Remote Technical Standards) - HOW to implement it technically  
3. ISO 27001 (Information Security) - How to do it SECURELY

FRAMEWORK REFERENCE GUIDE:
{framework_context}

INSTRUCTIONS:
- When answering questions, reference specific sections from relevant frameworks
- Show how frameworks interconnect (e.g., "LCCP requires X, implemented via RTS Y, with security from ISO Z")
- Provide practical guidance operators can implement
- Always cite framework sections and requirement IDs
- If information spans multiple frameworks, explain the relationships
- Be precise and avoid speculation

TONE: Professional, regulatory, practical guidance"""


def extract_search_terms(user_question):
    """
    Extract key search terms from user question
    """
    # Simple keyword extraction - can be enhanced with NLP
    keywords = []
    question_lower = user_question.lower()
    
    # Common regulatory terms
    regulatory_terms = {
        "customer": ["customer", "player", "user", "account"],
        "security": ["security", "encryption", "protected", "safe"],
        "verification": ["verify", "verification", "identity", "age", "kyc"],
        "funds": ["funds", "money", "balance", "payment", "deposit", "withdrawal"],
        "risk": ["risk", "compliance", "requirement", "must", "shall"],
        "reporting": ["report", "notify", "incident", "event", "breach"],
        "access": ["access", "permission", "role", "authentication", "control"],
        "audit": ["audit", "review", "assessment", "test", "control"],
    }
    
    for term, variations in regulatory_terms.items():
        if any(var in question_lower for var in variations):
            keywords.append(term)
    
    return keywords


# Example usage:
if __name__ == "__main__":
    print("Cross-Framework Index Builder Loaded")
    print("Ready to build searchable regulatory framework context")
