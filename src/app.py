import copy

import uvicorn

from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from criteria_builder import criteria_builder
from criteria_verifier import verify_round
from cv_validator import validate_cvs
from doc_parser import parse_directory
from output_handler import make_output_handler, history

CVS_DIR_PATH = "../cvs"


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

        if len(context) < 2:


            with response.create_single_choice() as choice:
                text = str(context[-1])
                with choice.create_stage("Identifying matching criteria") as prepare_stage:
                    vacancy = await make_output_handler(prepare_stage).ainvoke(criteria_builder.astream(text))
                with choice.create_stage("Loading CVs") as loading_stage:
                    cvs = validate_cvs(
                        directory_parser=parse_directory,
                        path=CVS_DIR_PATH,
                    )
                    loading_stage.append_content(
                        f"Recursively loaded {len(cvs)} CVs from directory `{CVS_DIR_PATH}`."
                    )
                with choice.create_stage("The Game") as game_stage:
                    await make_output_handler(game_stage, root_choice=choice).ainvoke(verify_round.astream(
                        {
                            'vacancy': vacancy,
                            'cvs': cvs,
                            'cvs_per_pack': 6,
                            'top_n_per_pack': 1,
                            'finalize_on': 5,
                        }
                    ))

        else:
            context.extend(history)
            model = ChatOpenAI(model='gpt-4o')
            with response.create_single_choice() as choice:
                await make_output_handler(choice).ainvoke(
                    model.astream(
                        str(context)
                    )
                )
        await response.aflush()


app = DIALApp()
app.add_chat_completion("hari", HariApplication())

# Run builded app
if __name__ == "__main__":
    uvicorn.run(app, port=5000, host="0.0.0.0")
