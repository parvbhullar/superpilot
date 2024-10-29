# Given data
data = {
    'message': 'As an expert in preservation architecture, I focus on the significance of historical events in shaping community identity and heritage. One of the most important historical events of the 21st century is the September 11 attacks in 2001. This tragic event not only resulted in a profound loss of life but also led to significant changes in global security policies, urban planning, and architectural design.\n\nIn the aftermath, there was a heightened emphasis on resilience in building design, particularly in urban areas. The reconstruction of the World Trade Center site, including the National September 11 Memorial & Museum, serves as a poignant reminder of the event and reflects a commitment to preserving memory while fostering community healing. \n\nMoreover, the event catalyzed a broader conversation about the role of architecture in memorializing history and addressing contemporary security needs. This has influenced preservation efforts in historic commercial buildings across Midwestern communities, where balancing historical integrity with modern utility is crucial for revitalizing local identities. \n\nUnderstanding such events is essential for communities as they navigate their historical narratives and future growth, ensuring that they honor their past while embracing resilience and sustainability in their architectural endeavors.',
    'ref_docs': [
        {
            'blurb': "66b78991dc71d42da1fa8485__precedenceresearch_chun.csv\n\r\ncategory:Energy and Power\nhistorical_year:2021-2022\nbase_year:2023\nestimated_years:2024-2034\nfrequently_asked_questions:[{'question': 'What will be the nuclear fusion market size?', 'answer': 'The global nuclear fusion market size is poised to reach around USD 843.46 billion by 2040.'}, {'question': 'What is nuclear fusion?",
            'source_type': 'file',
            'document_id': 'FILE_CONNECTOR__66b78991dc71d42da1fa8485',
            'semantic_identifier': '66b78991dc71d42da1fa8485__precedenceresearch_chun.csv'
        },
        # ... other ref_docs ...
    ],
    'citations': {
        '1': 473,
        '10': 2468,
        '17': 2607,
        '18': 2686,
        '29': 2847,
        '32': 2706,
        '34': 2727
    },
    'citation_num': {
        '1': 'FILE_CONNECTOR__66b78991dc71d42da1fa8485',
        '10': 'FILE_CONNECTOR__66b74b9a9f332e85ff0ede6c',
        '17': 'FILE_CONNECTOR__66b74b9a9f332e85ff0ede74',
        '18': 'FILE_CONNECTOR__66b76ee7dc71d42da1fa82f5',
        '29': 'FILE_CONNECTOR__66b76ed39f332e85ff0edf9a',
        '32': 'FILE_CONNECTOR__66ba06cca4bd9a26ae421bfa',
        '34': 'FILE_CONNECTOR__66b76ee7dc71d42da1fa833b'
    },
    'followup_questions': [
        'How do communities choose memorial designs after such events?',
        'What are key architectural principles for resilience in urban design?',
        'How can historic preservation balance modern needs with heritage?',
        'What role does community input play in memorial site development?',
        'How have security policies impacted architectural practices since 9/11?'
    ]
}

# Extract data
message = data['message']
ref_docs = data['ref_docs']
citations = data['citations']
citation_num = data['citation_num']

# Create a list of citations sorted by position in reverse order
citation_positions = []
for cit_num, pos in citations.items():
    citation_positions.append((pos, cit_num))
citation_positions.sort(reverse=True)

# Insert citation markers into the message
message_with_citations = message
for pos, cit_num in citation_positions:
    # Insert the citation marker [citation_number] at the specified position
    message_with_citations = (
        message_with_citations[:pos] + f'[{cit_num}]' + message_with_citations[pos:]
    )

# Map document IDs to reference documents
doc_id_to_ref_doc = {doc['document_id']: doc for doc in ref_docs}

# Build the references based on citation numbers
references = {}
for cit_num, doc_id in citation_num.items():
    ref_doc = doc_id_to_ref_doc.get(doc_id)
    if ref_doc:
        references[cit_num] = ref_doc
    else:
        # Handle missing references
        references[cit_num] = {'semantic_identifier': 'Reference not found', 'document_id': doc_id}

# Prepare the reference list
sorted_citation_numbers = sorted(references.keys(), key=int)
reference_list = []
for cit_num in sorted_citation_numbers:
    ref_doc = references[cit_num]
    reference = f"[{cit_num}] {ref_doc.get('semantic_identifier', 'No title')}"
    reference_list.append(reference)

# Output the message with citations and the reference list
print("Message with citations:")
print(message_with_citations)
print("\nReferences:")
for ref in reference_list:
    print(ref)
