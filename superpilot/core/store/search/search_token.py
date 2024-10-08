
from superpilot.core.store.search.models import SearchPipeline,SearchRequest,get_default_llm
async def get_document_search(query, kn_token, db_session, skip, limit):
    top_chunks = SearchPipeline(
        search_request=SearchRequest(
            query=query,
            offset=skip,
            limit=limit,
            human_selected_filters={
                "tags": [
                    {
                        "tag_key": "kn_token",
                        "tag_value": ",".join(kn_token),
                    }
                ]
            },
        ),
        user=None,
        llm=get_default_llm(),
        db_session=db_session,
    ).reranked_chunks
    return top_chunks