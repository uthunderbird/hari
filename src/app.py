import copy

import uvicorn

from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response
from langchain_core.output_parsers import StrOutputParser

from criteria_builder import criteria_builder
from criteria_verifier import verify_round
from output_handler import make_output_handler


# ChatCompletion is an abstract class for applications and model adapters
class HariApplication(ChatCompletion):

    def __init__(self):
        super().__init__()
        self.output_parser = StrOutputParser()
        self._llm_instance = None
        self._session = None
        self._toolkit = None
        self.specialists = {}

    async def chat_completion(self, request: Request, response: Response) -> None:

        context = copy.deepcopy(request.messages)

        with response.create_single_choice() as choice:
            text = str(context[-1])
            with choice.create_stage("Identifying matching criteria") as prepare_stage:
                vacancy = make_output_handler(prepare_stage).ainvoke(criteria_builder.astream(text))
            with choice.create_stage("The Game") as game_stage:
                make_output_handler(game_stage).ainvoke(verify_round.astream(vacancy))


app = DIALApp()
app.add_chat_completion("hari", HariApplication())

# Run builded app
if __name__ == "__main__":
    uvicorn.run(app, port=5000, host="0.0.0.0")
