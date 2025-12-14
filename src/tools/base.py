import pandas as pd
import uuid

class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: list[dict]
    ):
        self.name = name
        self.type = f'tool_{name}'
        self.id = f"tool_{name}_{uuid.uuid4().hex[:8]}"
        self.short_description = description
        self.parameters = parameters

    def prepare_params(self, task) -> dict:
        """
        Optional hook to derive API parameters from a task payload.
        """
        return {}
    
    @property
    def description(self):
        params_str = ", ".join([
            f"{p['name']}: {p['type']} ({p['description']})"
                for p in self.parameters
        ])
        return f"Tool name: {self.name}\nDescription: {self.short_description}\nParameters: {params_str}\n"

    async def api_function(self, **kwargs):
        """
        Execute the underlying API and return structured data.
        """
        raise NotImplementedError

    async def get_data(self, task):
        params = self.prepare_params(task)
        try:
            data = await self.api_function(**params)
            task.all_results.extend(data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []


class ToolResult:
    def __init__(self, name, description, data, source = ""):
        self.name = name
        self.description = description
        if isinstance(data, list) and len(data) == 1:
            data = data[0]
        self.data = data
        self.data_type = type(data)
        self.source = source  # str, data source

    def brief_str(self):
        # Example formatting helper (unused)
        return self.__str__()

    def get_full_string(self):
        if isinstance(self.data, pd.DataFrame):
            return self.data.to_string()
        else:
            return str(self.data)

    def __str__(self):
        base_string = f"Data name: {self.name}\nDescription: {self.description}\nSource: {self.source}\n"
        base_string += f"Data type: {type(self.data)}\n"
        if isinstance(self.data, pd.DataFrame):
            format_string = ""

            format_string += f"First five rows:\n{self.data.head().to_string()}\n"
        elif isinstance(self.data, dict):
            format_string = "Partial data preview: "
            format_string += str(self.data)[:500]
        elif isinstance(self.data, list):
            format_string = "Partial data preview: "
            format_string += str(self.data)[:500]
        else:
            format_string = "Partial data preview: "
            format_string += str(self.data)[:500]

        return base_string + format_string

    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash(self.name+self.description)
    
    def __eq__(self, other):
        return self.name == other.name and self.description == other.description