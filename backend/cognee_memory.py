import cognee


async def store_incident_memory(title, description, system, recommendation):

    incident_text = f"""
    Cybersecurity Incident

    Title:
    {title}

    Description:
    {description}

    Affected System:
    {system}

    Recommended Action:
    {recommendation}
    """

    await cognee.add(incident_text)

    await cognee.cognify()


async def search_incident_memory(query):

    results = await cognee.search(query)

    return results