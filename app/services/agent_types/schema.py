from typing_extensions import TypedDict, Annotated, List


class ExecutionSteps(TypedDict):
    agent_name: Annotated[str, ..., "Agent responsible for handling the step"]
    title: Annotated[str, ..., "Title of the step"]
    description: Annotated[str, ..., "Description of the step"]


class SolutionPlan(TypedDict):
    thought: Annotated[str, ..., "Thought process used to create the plan"]
    title: Annotated[str, ..., "Title of solution plan framed as an user intent"]
    steps: Annotated[List[ExecutionSteps], ..., "List of execution steps"]
