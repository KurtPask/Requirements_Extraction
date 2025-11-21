# Requirements Extraction Schema (v1)

This schema defines the JSON structure for extracting metadata and requirements from Navy policy documents, instructions, NTSPs, and related publications.  
Each processed PDF produces a JSON object containing:

```json
{
  "metadata": { ... },
  "requirements": [ ... ]
}

{
  "doc_id": "string",                   
  "file_name": "string",                
  "file_path": "string",                
  "source_url": "string|null",          

  "doc_type": "string|null",            
  "doc_number": "string|null",          
  "title": "string|null",               
  "issuing_organization": "string|null",
  "publication_date": "string|null",    
  "cancellation_date": "string|null",

  "classification": "string|null",      
  "distribution_statement": "string|null",

  "references": [
    "string"
  ],

  "summary": "string|null",             
  "keywords": [
    "string"
  ],

  "page_count": "number|null",
  "parsing_notes": "string|null"        
}

{
  "req_id": "string",                   
  "doc_id": "string",                   

  "source": {
    "page": "number|null",              
    "section_label": "string|null",     
    "section_heading": "string|null",
    "paragraph_id": "string|null"
  },

  "raw_text": "string",                 
  "normalized_text": "string|null",     

  "actor": "string|null",               
  "actor_level": "string|null",         
  "action": "string|null",              
  "object": "string|null",              

  "modality": "string|null",            
  "requirement_type": "string|null",    

  "system_or_program": "string|null",   
  "domain": "string|null",              

  "timeframe": "string|null",           
  "frequency": "string|null",           
  "conditions": "string|null",          

  "references": [
    "string"
  ],

  "priority": "string|null",            
  "verification_method": "string|null", 
  "notes": "string|null"
}

{
  "metadata": {
    "doc_id": "ntsp-fa18e-1995",
    "file_name": "ntsp_fa18e_example.pdf",
    "doc_type": "NTSP",
    "doc_number": "NTSP N88-95-001",
    "title": "F/A-18E/F TRAINING SYSTEM PLAN",
    "publication_date": "1995-07-01"
  },

  "requirements": [
    {
      "req_id": "ntsp-fa18e-1995-0001",
      "doc_id": "ntsp-fa18e-1995",

      "source": { 
        "page": 12, 
        "section_label": "3.2.1" 
      },

      "raw_text": "Commanding Officers shall ensure all aircrew complete the prescribed training syllabi prior to deployment.",

      "actor": "Commanding Officers",
      "actor_level": "unit",
      "action": "ensure all aircrew complete prescribed training syllabi",
      "object": "aircrew training syllabi",

      "modality": "shall",
      "requirement_type": "training",

      "system_or_program": "F/A-18E/F",
      "timeframe": "prior to deployment",

      "references": ["OPNAVINST 1500.76"]
    }
  ]
}
