import pydantic

class WikipediaContentRequestBase(pydantic.BaseModel):
    """Search Wikipedia and fetch the introduction of the most relevant article.
    
    Always use this if the user is asking for something that is likely on
    wikipedia.

    If the user has a typo in their search query, correct it before searching.

    For biographies, prefer searching for that individual person's article
    (using their full name).
    
    For events, prefer searching for the event name. 

    For other topics, prefer searching for the most common name of the topic in
    a way that would make sense for title of an encyclopedia article.

    Don't combine multiple search queries in one call: instead of 'Nikola Tesla
    WW1', search for 'Nikola Tesla' and 'World War 1' separately as two tool
    calls.

    Don't ask for 'first airing of X', instead ask just for 'X' since the API
    won't correctly handle the former and may return the wrong article. For
    example: 'first showing of The Matrix' should actually be requested with
    query 'The Matrix'.

    If you need the birthday of Marco Polo, don't ask for 'marco polo birthdate'
    and instead ask for 'Marco Polo'. The tool's search functionality is not
    ideal. Asking for base article text will get you further ahead.

    If you get an error in a function call, try to fix the arguments and repeat
    the call. Match the arguments strictly: don't assume the tool can handle
    arbitrary input, missing or misformatted parameters, etc.

    Don't make a call using data you do not have; ask for data you need in the
    first round of calls, then make the call you actually want to do in the next
    round. For example: if you try to compute difference between 'birth of Y'
    and 'start of Z', first make a request for an article about 'Y' and article
    about 'Z'; then once you receive the response to those requests, make a
    request for the difference between the dates; and only then send just a
    response without invoking a tool.
    """
    pass

class WikipediaContentRequestGemini(WikipediaContentRequestBase):
    # Gemini does not tolerate the schema if required=True is set.
    search_query: str = pydantic.Field(
        ...,
        description="Search query for finding the Wikipedia article",
    )

class WikipediaContentRequest(WikipediaContentRequestBase):
    search_query: str = pydantic.Field(
        ...,
        description="Search query for finding the Wikipedia article",
        required=True,
    )
