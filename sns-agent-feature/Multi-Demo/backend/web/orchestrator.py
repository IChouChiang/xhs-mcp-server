class Orchestrator:
    def __init__(self, ip_agent):
        self.ip_agent = ip_agent

    async def handle(self, user_id, text, mode="suggest"):
        return await self.ip_agent.run({
            "user_id": user_id,
            "user_input": text,
            "mode": mode
        })
